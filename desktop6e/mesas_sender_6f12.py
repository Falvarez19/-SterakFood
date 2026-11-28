"""Desktop -> Render: solo estado de lectura de mesas del respaldo local.

No envía ni recrea ventas, pagos, deudas, comprobantes ni asientos.
Si falla Internet conserva la fuente SQLite; al regresar envía la versión actual.
"""
from __future__ import annotations
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings
from pedidos.models import RespaldoMesasLocal
from desktop6c.models import DesktopLink
from desktop6c.security import clean_server_url, decrypt_token
from desktop6e.models import Desktop6eDevice


def _importe(value):
    try:
        value = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError('Precio inválido en respaldo local')
    if not value.is_finite() or value < 0 or value > Decimal('99999999.99'):
        raise ValueError('Precio de mesa fuera de rango')
    return value


def _resumen_cuentas(datos):
    """Solo lo indispensable para consulta; nunca copia IDs de cobro ni estado de caja."""
    if not isinstance(datos, dict) or len(datos) > 110:
        raise ValueError('Respaldo local de mesas inválido')
    mesas = {}
    for numero, cuenta in datos.items():
        num = str(numero)
        if not num.isdecimal() or not 1 <= int(num) <= 100 or not isinstance(cuenta, dict):
            raise ValueError('Mesa local inválida')
        lista = cuenta.get('items', [])
        if not isinstance(lista, list) or len(lista) > 250:
            raise ValueError('Productos de mesa inválidos')
        items = []
        for item in lista:
            if not isinstance(item, dict):
                raise ValueError('Producto local inválido')
            qty = Decimal(str(item.get('cantidad', 0)))
            if not qty.is_finite() or qty <= 0:
                continue
            if qty != qty.to_integral_value() or qty > 1000:
                raise ValueError('Cantidad de mesa inválida')
            nombre = str(item.get('nombre') or 'Producto').replace('\r', ' ').replace('\n',' ').strip()[:140]
            precio = _importe(item.get('precio', 0))
            items.append({'nombre': nombre or 'Producto', 'cantidad': int(qty), 'precio': str(precio)})
        if items:
            mozo = str(cuenta.get('mozo_nombre') or '').replace('\r',' ').replace('\n', ' ')[:100]
            mesas[str(int(num))] = {'mozo': mozo, 'items': items}
    return mesas


def enviar_estado():
    if not getattr(settings, 'STERAK_DESKTOP_MODE', False):
        return 'No se envía desde Render'
    link = DesktopLink.objects.first()
    if not link:
        return 'Sin vinculación Desktop'
    respaldo = RespaldoMesasLocal.objects.filter(pk=1).first()
    if respaldo is None:
        return 'Todavía sin respaldo de mesas'
    device, _ = Desktop6eDevice.objects.get_or_create(pk=1)
    server = clean_server_url(link.server_url)
    token = decrypt_token(link.token_ciphertext)
    snapshot = _resumen_cuentas(respaldo.datos)
    payload = {'schema': 1, 'installation_id': str(link.web_instance_id),
               'device_id': str(device.uid), 'version': respaldo.version,
               'mesas': snapshot}
    with requests.post(
        server + '/desktop/api/v1/mesas-6f12/', json=payload,
        headers={'Authorization': 'Bearer ' + token, 'Accept':'application/json'},
        timeout=(5, 12), allow_redirects=False,
    ) as response:
        if response.status_code not in (200, 201):
            if response.status_code == 503:
                raise ValueError('Render no tiene PostgreSQL persistente o está temporalmente inaccesible')
            raise ValueError('Render rechazó mesas con HTTP ' + str(response.status_code))
        if len(response.content) > 16384:
            raise ValueError('Acuse de mesas demasiado grande')
        data = response.json()
        if (data.get('status') != 'ok' or
            data.get('installation_id') != str(link.web_instance_id) or
            data.get('version') != respaldo.version):
            raise ValueError('Acuse de mesas incompatible: no se confirmó')
    return 'Estado de mesas sincronizado · versión ' + str(respaldo.version)
