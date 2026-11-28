"""SterakFood 6F.12A: replica SOLO LECTURA de mesas Desktop en Render.

El estado fuente es RespaldoMesasLocal de SQLite; no se crean Pedido,
DetallePedido, cobros, deuda, factura ni se modifica el Salón web.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from uuid import UUID

from django.conf import settings
from django.db import connection, transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from desktop6c.api import _authenticate, _denied
from desktop6c.models import WebInstallation
from desktop6e.models import Desktop6f12MesaMirror

VERSION = 1
MAX_BODY = 480_000
MAX_MESAS = 100
MAX_ITEMS = 250


def _respuesta(obj, status=200):
    result = JsonResponse(obj, status=status, json_dumps_params={'ensure_ascii': False})
    result['Cache-Control'] = 'no-store, private'
    result['X-Content-Type-Options'] = 'nosniff'
    return result


def _dinero(value):
    if type(value) not in (str, int, float):
        raise ValueError('Importe inválido')
    try:
        n = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError('Importe inválido') from exc
    if not n.is_finite() or n < 0 or n > Decimal('99999999.99'):
        raise ValueError('Importe fuera de rango')
    return n


def _validar_mesitas(mesas):
    if not isinstance(mesas, dict) or len(mesas) > MAX_MESAS:
        raise ValueError('Cantidad de mesas inválida')
    out = {}
    for key, mesa in mesas.items():
        if not isinstance(key, str) or not re.fullmatch(r'[1-9][0-9]{0,2}', key) or int(key) > 100:
            raise ValueError('Número de mesa inválido')
        if not isinstance(mesa, dict):
            raise ValueError('Mesa inválida')
        mozo = mesa.get('mozo', '')
        if not isinstance(mozo, str) or len(mozo) > 100:
            raise ValueError('Mozo inválido')
        raw_items = mesa.get('items')
        if not isinstance(raw_items, list) or not 1 <= len(raw_items) <= MAX_ITEMS:
            raise ValueError('Detalle de mesa inválido')
        items = []
        total_calculado = Decimal('0')
        for item in raw_items:
            if not isinstance(item, dict):
                raise ValueError('Producto inválido')
            nombre = item.get('nombre')
            cantidad = item.get('cantidad')
            if not isinstance(nombre, str) or not 1 <= len(nombre) <= 140:
                raise ValueError('Nombre de producto inválido')
            if type(cantidad) is not int or not 1 <= cantidad <= 1000:
                raise ValueError('Cantidad inválida')
            precio = _dinero(item.get('precio'))
            total_calculado += precio * cantidad
            items.append({'nombre': nombre, 'cantidad': cantidad, 'precio': str(precio)})
        if total_calculado > Decimal('9999999999.99'):
            raise ValueError('Total de mesa demasiado grande')
        out[key] = {'mozo': mozo, 'items': items, 'total': str(total_calculado)}
    return out


@csrf_exempt
@never_cache
@require_POST
def recibir_mesas(request):
    """Bearer del vínculo: snapshot absoluto e idempotente por dispositivo/versión."""
    if getattr(settings, 'STERAK_DESKTOP_MODE', False):
        return _respuesta({'error': 'Solo disponible en Render'}, 404)
    credencial = _authenticate(request)
    if credencial is None:
        return _denied()
    # Prohibimos estados compartidos efímeros.
    if connection.vendor != 'postgresql':
        return _respuesta({'error': 'Sin PostgreSQL persistente en Render: réplica bloqueada'}, 503)
    if len(request.body) > MAX_BODY:
        return _respuesta({'error': 'Estado demasiado grande'}, 413)
    try:
        body = json.loads(request.body.decode('utf-8'))
        if not isinstance(body, dict) or body.get('schema') != VERSION:
            raise ValueError('Versión de protocolo incorrecta')
        web_id = UUID(body['installation_id'])
        dispositivo = UUID(body['device_id'])
        version = body.get('version')
        if type(version) is not int or not 0 <= version < 2**63:
            raise ValueError('Versión de mesas inválida')
        snapshot = _validar_mesitas(body['mesas'])
    except (TypeError, ValueError, KeyError, UnicodeError, json.JSONDecodeError) as exc:
        return _respuesta({'error': str(exc)[:170]}, 400)

    instalacion, _ = WebInstallation.objects.get_or_create(pk=1)
    if web_id != instalacion.instance_id:
        return _respuesta({'error': 'Las mesas pertenecen a otro restaurante'}, 409)
    serializado = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    digest = hashlib.sha256(serializado.encode('utf-8')).hexdigest()

    with transaction.atomic():
        estado, nuevo = Desktop6f12MesaMirror.objects.select_for_update().get_or_create(
            device_id=dispositivo,
            defaults={'installation_id': web_id, 'version': version, 'snapshot': snapshot,
                      'digest': digest, 'token_label': credencial.label},
        )
        if not nuevo:
            if estado.installation_id != web_id:
                return _respuesta({'error': 'Terminal vinculada a otro restaurante'}, 409)
            if version < estado.version:
                return _respuesta({'error': 'Versión anterior: no se sobrescribieron mesas'}, 409)
            if version == estado.version and digest != estado.digest:
                return _respuesta({'error': 'Misma versión con contenido diferente: revisar respaldo'}, 409)
            estado.version = version
            estado.snapshot = snapshot
            estado.digest = digest
            estado.token_label = credencial.label
            estado.save(update_fields=['version','snapshot','digest','token_label','updated_at'])
    return _respuesta({'status': 'ok', 'version': version, 'installation_id': str(web_id),
                       'duplicado': not nuevo}, 200 if not nuevo else 201)


@never_cache
@require_GET
def estado_mesas_web(request):
    """Consulta protegida por la sesión del Salón web; no altera cuentas web."""
    if getattr(settings, 'STERAK_DESKTOP_MODE', False):
        return _respuesta({'error': 'Esta consulta es solamente para Render'}, 404)
    if not request.session.get('dashboard_auth'):
        return _respuesta({'error': 'Sesión del panel requerida'}, 403)
    if connection.vendor != 'postgresql':
        return _respuesta({'error': 'La base de Render no es PostgreSQL persistente'}, 503)
    now = timezone.now()
    dispositivos = []
    rows = Desktop6f12MesaMirror.objects.order_by('-updated_at')[:15]
    for row in rows:
        antiguedad = int(max(0, (now - row.updated_at).total_seconds()))
        dispositivos.append({
            'device_id': str(row.device_id),
            'etiqueta': row.token_label,
            'version': row.version,
            'segundos_desde_conexion': antiguedad,
            'conectada': antiguedad <= 90,
            'actualizado': timezone.localtime(row.updated_at).strftime('%d/%m/%Y %H:%M:%S'),
            'mesas': row.snapshot,
        })
    return _respuesta({'status': 'ok', 'dispositivos': dispositivos})
