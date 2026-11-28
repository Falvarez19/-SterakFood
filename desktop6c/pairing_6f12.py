"""Vinculación simplificada por código temporal, con una identidad por terminal.

El enlace canjeado NO genera Pedido, cobra, factura ni borra datos locales.
Los códigos nunca se guardan en claro; el token definitivo solo se envía una vez
por HTTPS y se cifra en el perfil de Windows.
"""
from __future__ import annotations

import base64
import json
import re
import secrets
from datetime import timedelta
from uuid import UUID

import requests
from django.conf import settings
from django.db import connection, transaction
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods

from .models import (DesktopAccessToken, DesktopLink, DesktopPairingCode,
                     DesktopRegisteredDevice, WebInstallation)
from .security import clean_server_url, encrypt_token, token_hash, TOKEN_RE

CODIGO_RE = re.compile(r'^[A-Z2-7]{20}$')
VIGENCIA_MINUTOS = 15


def _propietario(request):
    user = request.user
    return bool(user.is_authenticated and user.is_active and user.is_superuser)


def _web():
    return not getattr(settings, 'STERAK_DESKTOP_MODE', False)


def _respuesta(obj, status=200):
    res = JsonResponse(obj, status=status)
    res['Cache-Control'] = 'no-store, private'
    res['X-Content-Type-Options'] = 'nosniff'
    return res


def _normalizar_codigo(value):
    return re.sub(r'[\s-]+', '', str(value or '')).upper()


def _codigo_nuevo():
    # 100 bits aleatorios, cinco grupos de cuatro para escribirlo fácilmente.
    plano = base64.b32encode(secrets.token_bytes(13)).decode('ascii')[:20]
    return '-'.join(plano[i:i+4] for i in range(0, 20, 4))


@never_cache
@require_http_methods(['GET', 'POST'])
def equipos(request):
    """Solo propietario de la web; interfaz de códigos y revocación de PCs."""
    if not _web():
        return HttpResponseForbidden('Los equipos se administran desde la web del restaurante.')
    if not _propietario(request):
        return redirect('marca:acceso')
    instalacion, _ = WebInstallation.objects.get_or_create(pk=1)
    codigo = ''
    error = ''
    if request.method == 'POST':
        accion = str(request.POST.get('action') or '')
        if connection.vendor != 'postgresql':
            error = 'Hace falta PostgreSQL persistente en Render para vincular equipos de forma segura.'
        elif accion == 'crear':
            etiqueta = str(request.POST.get('label') or '').strip()
            if not 2 <= len(etiqueta) <= 80:
                error = 'Escribí un nombre para la caja, de 2 a 80 caracteres.'
            else:
                ahora = timezone.now()
                pendientes = DesktopPairingCode.objects.filter(
                    installation_id=instalacion.instance_id, redeemed_at__isnull=True,
                    expires_at__gt=ahora).count()
                if pendientes >= 10:
                    error = 'Hay 10 códigos pendientes. Esperá su vencimiento antes de generar más.'
                else:
                    for _ in range(5):
                        codigo = _codigo_nuevo()
                        codigo_hash = token_hash(_normalizar_codigo(codigo))
                        if not DesktopPairingCode.objects.filter(code_hash=codigo_hash).exists():
                            DesktopPairingCode.objects.create(
                                installation_id=instalacion.instance_id,
                                code_hash=codigo_hash, label=etiqueta,
                                expires_at=ahora + timedelta(minutes=VIGENCIA_MINUTOS),
                            )
                            break
                    else:
                        error = 'No se pudo generar el código. Volvé a intentarlo.'
        elif accion == 'revocar':
            try:
                uid = UUID(str(request.POST.get('device_uid', '')))
            except (ValueError, TypeError):
                error = 'Equipo inválido.'
            else:
                with transaction.atomic():
                    reg = DesktopRegisteredDevice.objects.select_for_update().filter(
                        device_uid=uid, installation_id=instalacion.instance_id).first()
                    if reg is None:
                        error = 'No existe esa computadora en este restaurante.'
                    elif reg.revoked_at is None:
                        DesktopAccessToken.objects.filter(pk=reg.token_id).update(active=False)
                        reg.revoked_at = timezone.now()
                        reg.save(update_fields=['revoked_at'])
        else:
            error = 'Acción desconocida.'
    activos = DesktopRegisteredDevice.objects.filter(
        installation_id=instalacion.instance_id).select_related('token').order_by('-created_at')[:150]
    pendientes = DesktopPairingCode.objects.filter(
        installation_id=instalacion.instance_id, redeemed_at__isnull=True,
        expires_at__gt=timezone.now()).order_by('-created_at')[:10]
    return render(request, 'desktop6c/equipos_6f12.html', {
        'codigo': codigo, 'error': error,
        'activos': activos, 'pendientes': pendientes,
        'instalacion': instalacion, 'minutos': VIGENCIA_MINUTOS,
    })


@csrf_exempt
@never_cache
@require_POST
def canjear(request):
    """API pública únicamente para consumir un secreto de 100 bits de un solo uso."""
    if not _web():
        return _respuesta({'error': 'Esta API solo existe en Render.'}, 404)
    if connection.vendor != 'postgresql':
        return _respuesta({'error': 'Vinculación no disponible: PostgreSQL persistente requerido.'}, 503)
    if len(request.body) > 4096:
        return _respuesta({'error': 'Solicitud demasiado grande.'}, 413)
    try:
        body = json.loads(request.body.decode('utf-8'))
        if not isinstance(body, dict) or body.get('schema') != 1:
            raise ValueError('Protocolo inválido')
        plano = _normalizar_codigo(body['codigo'])
        if not CODIGO_RE.fullmatch(plano):
            raise ValueError('Código inválido')
        device_uid = UUID(str(body['device_uid']))
    except (KeyError, TypeError, ValueError, UnicodeError, json.JSONDecodeError):
        return _respuesta({'error': 'Código o identidad de equipo inválida.'}, 400)

    instalacion, _ = WebInstallation.objects.get_or_create(pk=1)
    with transaction.atomic():
        registro = DesktopPairingCode.objects.select_for_update().filter(
            code_hash=token_hash(plano), installation_id=instalacion.instance_id).first()
        if (not registro or registro.redeemed_at is not None or
                registro.expires_at <= timezone.now()):
            return _respuesta({'error': 'Código vencido, consumido o incorrecto.'}, 400)
        anterior = DesktopRegisteredDevice.objects.select_for_update().filter(device_uid=device_uid).first()
        if anterior and anterior.installation_id != instalacion.instance_id:
            return _respuesta({'error': 'Identidad de equipo asociada a otro restaurante.'}, 409)
        token_plano = secrets.token_urlsafe(36)
        nuevo_token = DesktopAccessToken.objects.create(
            label=registro.label, token_hash=token_hash(token_plano), active=True)
        if anterior:
            # Recuperación si se perdió el acuse de un código anterior: un NUEVO
            # código autorizado rota la credencial, sin duplicar la ID de caja.
            DesktopAccessToken.objects.filter(pk=anterior.token_id).update(active=False)
            anterior.token = nuevo_token
            anterior.revoked_at = None
            anterior.label = registro.label
            anterior.save(update_fields=['token', 'revoked_at', 'label'])
        else:
            DesktopRegisteredDevice.objects.create(
                device_uid=device_uid, installation_id=instalacion.instance_id,
                token=nuevo_token, label=registro.label,
            )
        registro.redeemed_at = timezone.now()
        registro.token = nuevo_token
        registro.device_uid = device_uid
        registro.save(update_fields=['redeemed_at', 'token', 'device_uid'])
    # La credencial se entrega una sola vez; el servidor conserva únicamente su SHA256.
    return _respuesta({'status': 'ok', 'schema': 1,
                       'installation_id': str(instalacion.instance_id),
                       'device_uid': str(device_uid), 'token': token_plano}, 201)


def _hay_cuentas_locales():
    from pedidos.models import RespaldoMesasLocal, Pedido, CuentaCorriente
    # Una caja antigua sin vínculo puede contener ventas/deudas de otro negocio.
    # La instalación automática nunca debe mezclarlas con una vinculación nueva.
    if Pedido.objects.exists() or CuentaCorriente.objects.exists():
        return True
    res = RespaldoMesasLocal.objects.filter(pk=1).first()
    if not res or not isinstance(res.datos, dict):
        return False
    return any(isinstance(c, dict) and c.get('items') for c in res.datos.values())


@never_cache
@require_http_methods(['GET', 'POST'])
def vincular(request):
    """Vincula una PC nueva con URL y código; sin copiar tokens permanentes."""
    if _web():
        return HttpResponseForbidden('Vinculá la caja desde Desktop.')
    if not _propietario(request):
        return redirect('desktop6c:pair')
    if DesktopLink.objects.exists():
        return redirect('desktop6c:pair')
    error = ''
    if request.method == 'POST':
        url_raw = str(request.POST.get('server_url') or '').strip()
        codigo = _normalizar_codigo(request.POST.get('codigo'))
        try:
            if _hay_cuentas_locales():
                raise ValueError('Esta PC contiene mesas, ventas o cuentas locales. Hace falta migración asistida antes de vincularla.')
            if not CODIGO_RE.fullmatch(codigo):
                raise ValueError('Ingresá el código temporal completo.')
            url = clean_server_url(url_raw)
            from desktop6e.models import Desktop6eDevice
            device, _ = Desktop6eDevice.objects.get_or_create(pk=1)
            with requests.post(url + '/desktop/api/v1/vincular-codigo/',
                               json={'schema': 1, 'codigo': codigo, 'device_uid': str(device.uid)},
                               timeout=(5, 18), allow_redirects=False,
                               headers={'Accept': 'application/json'}) as response:
                if len(response.content) > 8192:
                    raise ValueError('Respuesta remota demasiado grande.')
                try:
                    data = response.json()
                except (ValueError, UnicodeError):
                    raise ValueError('Render no respondió correctamente.')
                if not isinstance(data, dict) or response.status_code != 201 or data.get('status') != 'ok':
                    raise ValueError(str(data.get('error', 'No se pudo vincular'))[:180])
            if data.get('schema') != 1 or data.get('device_uid') != str(device.uid):
                raise ValueError('La identidad de la respuesta no coincide con esta computadora.')
            instancia = UUID(data['installation_id'])
            token = data['token']
            if not isinstance(token, str) or not TOKEN_RE.fullmatch(token):
                raise ValueError('Render devolvió una clave incorrecta.')
            # Guardamos el token cifrado ANTES de descargar el catálogo. Si la red
            # falla, la vinculación sobrevive y el sincronizador la completa luego.
            if DesktopLink.objects.exists():
                raise ValueError('La PC ya está vinculada. No se reemplazó su restaurante.')
            DesktopLink.objects.create(server_url=url, web_instance_id=instancia,
                                       token_ciphertext=encrypt_token(token))
            from desktop6c.sync import run_sync
            try:
                run_sync()
            except Exception:
                # El sincronizador reintentará después; no volver a canjear el código.
                pass
            return redirect('desktop6c:pair')
        except (requests.RequestException, ValueError, TypeError, KeyError) as exc:
            error = str(exc)[:240]
        except Exception as exc:
            # No revelar credenciales, contenido de respuestas ni detalles internos.
            error = 'No se pudo completar la vinculación. Revisá la conexión y el estado del equipo.'
    return render(request, 'desktop6c/vincular_codigo_6f12.html', {'error': error})
