"""Panel de alta fiscal sin CMD: endpoints exclusivamente para propietario.

Nunca imprime ni emite comprobantes. Las llamadas WSAA/WSFE son solo consulta.
"""
from __future__ import annotations

import re
from pathlib import Path

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST

from pedidos.models import ConfiguracionFiscal
from .models import ArcaCredencial
from .views import autorizado
from .arca_vault_5a import (
    ConfiguracionSeguraError, MAX_P12_BYTES, abrir_p12, cifrar_archivo,
    verificar_row, boveda_disponible,
)


def _permiso(request):
    if not autorizado(request):
        return HttpResponseForbidden('Acceso exclusivo del propietario.')
    return None


def _entorno(request):
    valor = (request.POST.get('entorno') or '').strip().lower()
    if valor not in ('homologacion', 'produccion'):
        raise ConfiguracionSeguraError('Elegí homologación o producción.')
    return valor


def _datos_fiscales():
    fiscal, _ = ConfiguracionFiscal.objects.get_or_create(pk=1)
    if not fiscal.cuit or not fiscal.punto_venta_referencia:
        raise ConfiguracionSeguraError('Primero guardá CUIT y punto de venta en Datos fiscales.')
    return fiscal


def _error_generico(exc):
    # No propagar posibles respuestas SOAP, tokens, P12 o rutas internas.
    if isinstance(exc, ConfiguracionSeguraError):
        return str(exc)[:280]
    return 'No se pudo validar con ARCA. Comprobá autorizaciones, certificado y conexión.'


@never_cache
@csrf_protect
@sensitive_post_parameters('password_p12')
@require_POST
def cargar_certificado_5a(request):
    permiso = _permiso(request)
    if permiso:
        return permiso
    try:
        if not boveda_disponible():
            raise ConfiguracionSeguraError('La bóveda cifrada todavía no está habilitada en este servidor.')
        env = _entorno(request)
        fiscal = _datos_fiscales()
        fichero = request.FILES.get('certificado_p12')
        if not fichero or not fichero.name.lower().endswith(('.p12', '.pfx')):
            raise ConfiguracionSeguraError('Seleccioná un archivo .p12 o .pfx válido.')
        if not 0 < fichero.size <= MAX_P12_BYTES:
            raise ConfiguracionSeguraError('El archivo debe pesar menos de 256 KB.')
        password = request.POST.get('password_p12', '')
        contenido = fichero.read(MAX_P12_BYTES + 1)
        _clave, _cert, expiracion, huella = abrir_p12(contenido, password)
        cifrado = cifrar_archivo(contenido, password)
        nombre = Path(fichero.name.replace('\\', '/')).name[:100]
        ingresos = (request.POST.get('ingresos_brutos') or '').strip()
        inicio = (request.POST.get('inicio_actividades') or '').strip()
        if len(ingresos) > 60 or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', inicio):
            raise ConfiguracionSeguraError('Completá Ingresos Brutos y la fecha de inicio (AAAA-MM-DD).')
        from datetime import date
        try:
            inicio_fecha = date.fromisoformat(inicio)
        except ValueError as exc:
            raise ConfiguracionSeguraError('La fecha de inicio no es válida.') from exc
        if inicio_fecha > date.today():
            raise ConfiguracionSeguraError('El inicio de actividades no puede ser futuro.')
        with transaction.atomic():
            fila, _ = ArcaCredencial.objects.select_for_update().get_or_create(
                entorno=env, defaults={
                    'cuit': fiscal.cuit, 'punto_venta': fiscal.punto_venta_referencia,
                    'secreto_cifrado': cifrado, 'huella_sha256': huella,
                    'vencimiento': expiracion,
                })
            fila.cuit = fiscal.cuit
            fila.punto_venta = fiscal.punto_venta_referencia
            fila.secreto_cifrado = cifrado
            fila.nombre_archivo = nombre
            fila.huella_sha256 = huella
            fila.vencimiento = expiracion
            fila.ingresos_brutos = ingresos
            fila.inicio_actividades = inicio_fecha
            fila.verificada = False
            fila.activa = False
            fila.ultimo_chequeo = None
            fila.save()
        messages.success(request, 'Certificado guardado cifrado. Ahora comprobá el acceso a ARCA.')
    except (ConfiguracionSeguraError, OSError) as exc:
        messages.error(request, _error_generico(exc))
    return redirect('marca:arca_propietario')


@never_cache
@csrf_protect
@require_POST
def verificar_arca_5a(request):
    permiso = _permiso(request)
    if permiso:
        return permiso
    try:
        env = _entorno(request)
        fila = ArcaCredencial.objects.get(entorno=env)
        fiscal = _datos_fiscales()
        # Sin emitir comprobantes; solo FEDummy, WSAA y FEParamGetPtosVenta.
        verificar_row(fila, fiscal)
        from django.utils import timezone
        actualizados = ArcaCredencial.objects.filter(
            pk=fila.pk, huella_sha256=fila.huella_sha256, cuit=fila.cuit,
            punto_venta=fila.punto_venta).update(
                verificada=True, ultimo_chequeo=timezone.now())
        if actualizados != 1:
            raise ConfiguracionSeguraError('El certificado cambió durante la verificación. Volvé a comprobar.')
        messages.success(request, 'ARCA confirmó autenticación WSAA, WSFEv1 y punto de venta. Podés activar.')
    except ArcaCredencial.DoesNotExist:
        messages.error(request, 'Primero cargá un certificado para el entorno elegido.')
    except Exception as exc:
        # Si falla verificación, nunca mantener activo un certificado anterior.
        if 'fila' in locals():
            ArcaCredencial.objects.filter(pk=fila.pk).update(verificada=False, activa=False)
        messages.error(request, _error_generico(exc))
    return redirect('marca:arca_propietario')


@never_cache
@csrf_protect
@require_POST
def activar_arca_5a(request):
    permiso = _permiso(request)
    if permiso:
        return permiso
    try:
        env = _entorno(request)
        if request.POST.get('confirmo') != 'SI':
            raise ConfiguracionSeguraError('Confirmá que sos el propietario y que querés habilitar la emisión.')
        if env == 'produccion' and request.POST.get('confirmo_produccion') != 'SI':
            raise ConfiguracionSeguraError('Confirmá expresamente la activación de comprobantes reales.')
        if env == 'produccion':
            raise ConfiguracionSeguraError('Producción fiscal bloqueada en 5J hasta homologación, auditoría y verificación real de impresión.')
        fila = ArcaCredencial.objects.get(entorno=env)
        fiscal = _datos_fiscales()
        # Revalidar contra ARCA justo antes de la activación (sin CAE).
        verificar_row(fila, fiscal)
        huella_validada = fila.huella_sha256
        from django.utils import timezone
        with transaction.atomic():
            ArcaCredencial.objects.select_for_update().all().update(activa=False)
            fila = ArcaCredencial.objects.select_for_update().get(pk=fila.pk)
            if fila.huella_sha256 != huella_validada or fila.cuit != fiscal.cuit or fila.punto_venta != fiscal.punto_venta_referencia:
                raise ConfiguracionSeguraError('Los datos fiscales cambiaron durante la comprobación. Volvé a verificar.')
            fila.verificada = True
            fila.activa = True
            fila.ultimo_chequeo = timezone.now()
            fila.save(update_fields=['verificada', 'activa', 'ultimo_chequeo'])
        messages.success(request, 'Facturación activada para este negocio y entorno. La emisión sigue siendo manual desde el POS.')
    except ArcaCredencial.DoesNotExist:
        messages.error(request, 'No se encontró certificado para el entorno elegido.')
    except Exception as exc:
        messages.error(request, _error_generico(exc))
    return redirect('marca:arca_propietario')


@never_cache
@csrf_protect
@require_POST
def desactivar_arca_5a(request):
    permiso = _permiso(request)
    if permiso:
        return permiso
    env = request.POST.get('entorno', '').strip().lower()
    if env not in ('homologacion', 'produccion'):
        messages.error(request, 'Entorno no reconocido.')
    else:
        ArcaCredencial.objects.filter(entorno=env).update(activa=False)
        messages.success(request, 'Facturación desactivada para el entorno seleccionado.')
    return redirect('marca:arca_propietario')
