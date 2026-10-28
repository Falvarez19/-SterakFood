"""Panel seguro para impresoras y consulta remota de la ticketera Windows.
No imprime desde Render: la PC del negocio sigue conectándose a la impresora local.
"""
import hashlib
import ipaddress
import json
import secrets
from datetime import timedelta

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .models import ConfiguracionImpresorasPOS


def _config():
    cfg, _ = ConfiguracionImpresorasPOS.objects.get_or_create(pk=1)
    return cfg


def _resultado(cfg):
    return {
        'caja_windows': cfg.caja_windows,
        'ip_cocina': cfg.ip_cocina,
        'ip_barra': cfg.ip_barra,
        'ancho_ticket': cfg.ancho_ticket,
        'vinculada': bool(cfg.token_hash),
        'ultima_conexion': cfg.ultima_conexion.isoformat() if cfg.ultima_conexion else None,
    }


def _admin(request):
    return bool(request.session.get('dashboard_auth'))


@require_GET
def impresoras_obtener(request):
    if not _admin(request):
        return JsonResponse({'status':'error','mensaje':'Ingresá al panel.'}, status=403)
    return JsonResponse({'status':'ok', 'configuracion':_resultado(_config())})


@require_POST
def impresoras_guardar(request):
    if not _admin(request):
        return JsonResponse({'status':'error','mensaje':'No autorizado'}, status=403)
    try:
        data = json.loads(request.body.decode('utf-8'))
        caja = str(data.get('caja_windows', '')).strip()
        cocina = str(data.get('ip_cocina', '')).strip()
        barra = str(data.get('ip_barra', '')).strip()
        ancho = int(data.get('ancho_ticket',32))
        if not (1 <= len(caja) <= 120) or any(ord(c) < 32 for c in caja):
            raise ValueError('Escribí un nombre de impresora válido para Windows.')
        # Una IP local por sector, jamás URLs ni nombres de host arbitrarios.
        for ip in (cocina, barra):
            direccion = ipaddress.ip_address(ip)
            if direccion.version != 4 or not (direccion.is_private or direccion.is_link_local):
                raise ValueError('Usá una IP privada de la red local (por ejemplo 192.168.x.x).')
        if ancho not in (32, 42, 48):
            raise ValueError('Elegí un ancho de 32, 42 o 48 caracteres.')
    except (ValueError, TypeError, KeyError) as exc:
        return JsonResponse({'status':'error','mensaje':str(exc)},status=400)
    cfg = _config()
    cfg.caja_windows, cfg.ip_cocina, cfg.ip_barra = caja, cocina, barra
    cfg.ancho_ticket = ancho
    cfg.save(update_fields=['caja_windows','ip_cocina','ip_barra','ancho_ticket','actualizado'])
    return JsonResponse({'status':'ok','mensaje':'Configuración guardada','configuracion':_resultado(cfg)})


@require_POST
def impresoras_vincular(request):
    if not _admin(request):
        return JsonResponse({'status':'error','mensaje':'No autorizado'},status=403)
    # Rotar la clave invalida la vinculación anterior (intencional).
    token = secrets.token_urlsafe(36)
    cfg = _config()
    cfg.token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    cfg.ultima_conexion = None
    cfg.save(update_fields=['token_hash','ultima_conexion','actualizado'])
    return JsonResponse({
        'status':'ok',
        'nombre_archivo':'VINCULAR_IMPRESORA_STERAKFOOD.json',
        'archivo': {'servidor': request.build_absolute_uri('/').rstrip('/'), 'token':token},
        'mensaje':'Descargá el archivo y colocalo dentro de datos_locales en la PC del negocio. No lo subas a GitHub ni lo compartas.',
    })


@require_GET
def ticketera_configuracion_api(request):
    cfg = _config()
    token = request.headers.get('X-Config-Impresora-Token','')
    if not cfg.token_hash or len(token) < 32:
        return JsonResponse({'status':'error','mensaje':'Sin vinculación'},status=403)
    recibido = hashlib.sha256(token.encode('utf-8')).hexdigest()
    if not secrets.compare_digest(recibido,cfg.token_hash):
        return JsonResponse({'status':'error','mensaje':'Clave inválida'}, status=403)
    ahora = timezone.now()
    if not cfg.ultima_conexion or ahora-cfg.ultima_conexion > timedelta(minutes=1):
        cfg.ultima_conexion = ahora
        cfg.save(update_fields=['ultima_conexion'])
    return JsonResponse({'status':'ok','configuracion':_resultado(cfg)})
