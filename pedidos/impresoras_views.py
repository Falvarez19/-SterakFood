
"""Configuración web de impresoras 6F3. Render nunca accede al hardware USB."""
import hashlib
import ipaddress
import json
import secrets
from datetime import timedelta

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .models import ConfiguracionImpresorasPOS


CAMPOS_6F3 = ('caja_modo', 'caja_windows', 'caja_ip', 'cocina_modo',
              'cocina_windows', 'ip_cocina', 'barra_modo', 'barra_windows',
              'ip_barra', 'ancho_ticket')


def validar_rutas_6f3(data):
    """Validación unificada en web y Desktop; nunca imprime desde Render."""
    res = {}
    for sector in ('caja', 'cocina', 'barra'):
        metodo = str(data.get(sector + '_modo', {'caja':'windows', 'cocina':'tcp', 'barra':'tcp'}[sector])).strip()
        if metodo not in ('windows', 'tcp', 'off'):
            raise ValueError('Método de impresión incorrecto para ' + sector + '.')
        campo_windows = 'caja_windows' if sector == 'caja' else sector + '_windows'
        campo_ip = {'caja': 'caja_ip', 'cocina': 'ip_cocina', 'barra': 'ip_barra'}[sector]
        nombre = str(data.get(campo_windows) or '').strip()
        ip = str(data.get(campo_ip) or '').strip()
        if len(nombre) > 120 or any(ord(c) < 32 for c in nombre):
            raise ValueError('Nombre Windows inválido para ' + sector + '.')
        if metodo == 'windows' and not nombre:
            raise ValueError('Elegí o escribí una impresora de Windows para ' + sector + '.')
        if metodo == 'tcp':
            try:
                direccion = ipaddress.ip_address(ip)
                if direccion.version != 4 or not (direccion.is_private or direccion.is_link_local) or direccion.is_loopback:
                    raise ValueError()
            except ValueError as exc:
                raise ValueError('Indicá una IPv4 privada válida para ' + sector + '.') from exc
            ip = str(direccion)
        # Conservo datos históricos de rutas desactivadas; no los usarán los agentes.
        res[sector + '_modo'] = metodo
        res[campo_windows] = nombre
        if ip:
            try:
                direccion = ipaddress.ip_address(ip)
                if direccion.version != 4 or not (direccion.is_private or direccion.is_link_local) or direccion.is_loopback:
                    raise ValueError()
                ip = str(direccion)
            except ValueError as exc:
                raise ValueError('IP de ' + sector + ' inválida.') from exc
        res[campo_ip] = (ip or None) if sector == 'caja' else (ip or str(data.get(campo_ip) or '').strip())
    ancho = int(data.get('ancho_ticket', 32))
    if ancho not in (32,42,48):
        raise ValueError('Ancho de ticket inválido.')
    res['ancho_ticket'] = ancho
    return res


def _config():
    cfg, _ = ConfiguracionImpresorasPOS.objects.get_or_create(pk=1)
    return cfg


def _resultado(cfg):
    datos = {k: getattr(cfg, k) for k in CAMPOS_6F3}
    datos.update({'vinculada': bool(cfg.token_hash),
                  'ultima_conexion': cfg.ultima_conexion.isoformat() if cfg.ultima_conexion else None})
    return datos


def _admin(request):
    return bool(request.session.get('dashboard_auth'))


@require_GET
def impresoras_obtener(request):
    if not _admin(request):
        return JsonResponse({'status': 'error', 'mensaje': 'Ingresá al panel.'}, status=403)
    return JsonResponse({'status': 'ok', 'configuracion': _resultado(_config())})


@require_POST
def impresoras_guardar(request):
    if not _admin(request):
        return JsonResponse({'status': 'error', 'mensaje': 'No autorizado'}, status=403)
    try:
        data = json.loads(request.body.decode('utf-8'))
        if not isinstance(data,dict):
            raise ValueError('Se esperaba un objeto JSON.')
        validated = validar_rutas_6f3(data)
    except (ValueError, TypeError, KeyError) as exc:
        return JsonResponse({'status': 'error', 'mensaje': str(exc)}, status=400)
    cfg = _config()
    for key, value in validated.items():
        setattr(cfg,key,value)
    cfg.save(update_fields=[*validated.keys(), 'actualizado'])
    return JsonResponse({'status': 'ok', 'mensaje': 'Configuración guardada', 'configuracion': _resultado(cfg)})


@require_POST
def impresoras_vincular(request):
    if not _admin(request):
        return JsonResponse({'status': 'error', 'mensaje': 'No autorizado'}, status=403)
    token = secrets.token_urlsafe(36)
    cfg = _config()
    cfg.token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    cfg.ultima_conexion = None
    cfg.save(update_fields=['token_hash', 'ultima_conexion', 'actualizado'])
    return JsonResponse({
        'status': 'ok',
        'nombre_archivo': 'VINCULAR_IMPRESORA_STERAKFOOD.json',
        'archivo': {'servidor': request.build_absolute_uri('/').rstrip('/'), 'token': token},
        'mensaje': 'Guardá el archivo de vinculación únicamente en la PC del negocio.',
    })


@require_GET
def ticketera_configuracion_api(request):
    cfg = _config()
    token = request.headers.get('X-Config-Impresora-Token', '')
    if not cfg.token_hash or len(token) < 32:
        return JsonResponse({'status': 'error', 'mensaje': 'Sin vinculación'}, status=403)
    recibido = hashlib.sha256(token.encode('utf-8')).hexdigest()
    if not secrets.compare_digest(recibido, cfg.token_hash):
        return JsonResponse({'status': 'error', 'mensaje': 'Clave inválida'}, status=403)
    ahora = timezone.now()
    if not cfg.ultima_conexion or ahora - cfg.ultima_conexion > timedelta(minutes=1):
        cfg.ultima_conexion = ahora
        cfg.save(update_fields=['ultima_conexion'])
    return JsonResponse({'status': 'ok', 'configuracion': _resultado(cfg)})
