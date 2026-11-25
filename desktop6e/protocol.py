"""Contrato estricto cliente/servidor. Independiente del motor de base de datos."""
import hashlib
import json
import re
from decimal import Decimal
from uuid import UUID

VERSION = 1
TIPOS = {'venta.salon', 'pedido.para_llevar', 'cobro.para_llevar',
         'cuenta.estado', 'cuenta.movimiento', 'caja.corte'}
_ORIGEN = re.compile(r'^[a-z0-9][a-z0-9:_\-.]{0,109}$')


def canonical(payload):
    return json.dumps(payload, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha(payload):
    return hashlib.sha256(canonical(payload)).hexdigest()


def validar(paquete):
    if not isinstance(paquete, dict) or set(paquete) != {'schema','installation_id','device_id','event_id','tipo','origen','payload','digest'}:
        raise ValueError('Estructura de evento incorrecta.')
    if type(paquete['schema']) is not int or paquete['schema'] != VERSION:
        raise ValueError('Versión 6E incompatible.')
    for key in ('installation_id','device_id','event_id'):
        try: UUID(str(paquete[key]))
        except (ValueError,TypeError,AttributeError):
            raise ValueError('Identificador de evento inválido.')
    if paquete['tipo'] not in TIPOS or not isinstance(paquete['origen'],str) or not _ORIGEN.fullmatch(paquete['origen']):
        raise ValueError('Tipo u origen no permitido.')
    p=paquete['payload']
    if not isinstance(p,dict) or p.get('tipo')!=paquete['tipo'] or p.get('origen')!=paquete['origen']:
        raise ValueError('Datos de operación inconsistentes.')
    if not isinstance(paquete['digest'],str) or len(paquete['digest'])!=64 or sha(p)!=paquete['digest']:
        raise ValueError('El hash del evento no coincide.')
    if len(canonical(p)) > 48*1024:
        raise ValueError('Evento demasiado grande.')
    # El resumen monetario viaja como string decimal; rechazar NaN y números negativos.
    if 'total' in p:
        try: cantidad=Decimal(p['total'])
        except (TypeError,ValueError): raise ValueError('Importe inválido.')
        if not cantidad.is_finite() or cantidad < 0 or cantidad > Decimal('999999999.99'):
            raise ValueError('Importe fuera de rango.')
    return True
