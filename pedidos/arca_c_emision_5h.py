"""Factura C, *únicamente* ensayos de homologación (no ventas POS).

Puede solicitar CAE de prueba a ARCA, pero JAMÁS usa endpoints de producción.
Las credenciales se reciben desde la bóveda; no se persisten en este módulo.
"""
from __future__ import annotations

import base64
import json
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from xml.etree import ElementTree as ET

WSFE_NS = 'http://ar.gov.afip.dif.FEV1/'
TIPO = 11
MAX_ENSAYO = Decimal('1000.00')


class FacturaCEnsayoError(ValueError):
    pass


class FacturaCEnsayoRechazada(FacturaCEnsayoError):
    pass


class FacturaCEnsayoIncierta(FacturaCEnsayoError):
    pass


def _add(parent, key, value):
    node = ET.SubElement(parent, f'{{{WSFE_NS}}}{key}')
    node.text = str(value)
    return node


def _first(root, name):
    return next((n for n in root.iter() if n.tag.rsplit('}', 1)[-1] == name), None)


def _value(root, name, default=''):
    node = _first(root, name) if root is not None else None
    return (node.text or '').strip() if node is not None else default


def total_ensayo(value):
    v = str(value).strip()
    if not re.fullmatch(r'[0-9]{1,4}(?:[.,][0-9]{1,2})?', v):
        raise FacturaCEnsayoError('Importe de prueba inválido: ingresá entre $1 y $1.000.')
    try:
        value = Decimal(v.replace(',', '.')).quantize(Decimal('.01'))
    except InvalidOperation as exc:
        raise FacturaCEnsayoError('Importe de prueba inválido.') from exc
    if not Decimal('1.00') <= value <= MAX_ENSAYO:
        raise FacturaCEnsayoError('El ensayo permite importes entre $1 y $1.000.')
    return value


def _auth(root, token, sign, cuit):
    if not token or not sign or not re.fullmatch(r'[0-9]{11}', str(cuit)):
        raise FacturaCEnsayoError('No están disponibles las credenciales de homologación.')
    auth = ET.SubElement(root, f'{{{WSFE_NS}}}Auth')
    for key, val in [('Token', token), ('Sign', sign), ('Cuit', cuit)]:
        _add(auth, key, val)


def armar_solicitud_c(token, sign, cuit, pv, numero, importe, fecha, *, entorno):
    if entorno != 'homologacion':
        raise FacturaCEnsayoError('Se bloqueó una emisión fuera de homologación.')
    if type(pv) is not int or not 1 <= pv <= 99999:
        raise FacturaCEnsayoError('Punto de venta de prueba inválido.')
    if type(numero) is not int or not 1 <= numero <= 99999999:
        raise FacturaCEnsayoError('Número de ensayo inválido.')
    try:
        datetime.strptime(fecha, '%Y%m%d')
    except (TypeError, ValueError) as exc:
        raise FacturaCEnsayoError('Fecha de comprobante inválida.') from exc
    importe = total_ensayo(importe)
    op = ET.Element(f'{{{WSFE_NS}}}FECAESolicitar')
    _auth(op, token, sign, cuit)
    req = ET.SubElement(op, f'{{{WSFE_NS}}}FeCAEReq')
    cab = ET.SubElement(req, f'{{{WSFE_NS}}}FeCabReq')
    for k, v in (('CantReg', 1), ('PtoVta', pv), ('CbteTipo', TIPO)):
        _add(cab, k, v)
    det = ET.SubElement(req, f'{{{WSFE_NS}}}FeDetReq')
    fila = ET.SubElement(det, f'{{{WSFE_NS}}}FECAEDetRequest')
    # Ensayos limitados a CONSUMIDOR FINAL, bienes, PES y sin desglose IVA.
    # No sirve para facturar servicios, exportaciones ni receptores especiales.
    campos = [
        ('Concepto', 1), ('DocTipo', 99), ('DocNro', 0),
        ('CbteDesde', numero), ('CbteHasta', numero), ('CbteFch', fecha),
        ('ImpTotal', f'{importe:.2f}'), ('ImpTotConc', '0.00'),
        ('ImpNeto', f'{importe:.2f}'), ('ImpOpEx', '0.00'),
        ('ImpTrib', '0.00'), ('ImpIVA', '0.00'),
        ('MonId', 'PES'), ('MonCotiz', 1), ('CondicionIVAReceptorId', 5),
    ]
    for k, v in campos:
        _add(fila, k, v)
    return op


def interpretar_emision_c(root, numero):
    """Solo confirmamos autorización al recibir Resultado=A, CAE y vencimiento."""
    if not isinstance(root, ET.Element):
        raise FacturaCEnsayoIncierta('Respuesta incompleta: consultar en ARCA.')
    if _first(root, 'Fault') is not None:
        raise FacturaCEnsayoIncierta('ARCA devolvió un error SOAP: consultar antes de reintentar.')
    det = _first(root, 'FECAEDetResponse')
    if det is None:
        raise FacturaCEnsayoIncierta('ARCA no entregó detalle: consultar antes de reintentar.')
    resultado = _value(det, 'Resultado')
    cae = _value(det, 'CAE')
    vence = _value(det, 'CAEFchVto')
    desde = _value(det, 'CbteDesde')
    hasta = _value(det, 'CbteHasta')
    if resultado == 'R':
        raise FacturaCEnsayoRechazada('ARCA rechazó el comprobante de homologación. Revisar observaciones en ARCA.')
    if resultado != 'A' or not re.fullmatch(r'[0-9]{10,20}', cae) or not re.fullmatch(r'[0-9]{8}', vence):
        raise FacturaCEnsayoIncierta('La respuesta no confirmó un CAE válido; consultar antes de reintentar.')
    if (desde and desde != str(numero)) or (hasta and hasta != str(numero)):
        raise FacturaCEnsayoIncierta('La numeración de respuesta no coincide; investigar en ARCA.')
    return {'cae': cae, 'vencimiento': vence}


def armar_consulta_c(token, sign, cuit, pv, numero, *, entorno):
    if entorno != 'homologacion':
        raise FacturaCEnsayoError('Las consultas 5H solo funcionan en homologación.')
    if not 1 <= int(pv) <= 99999 or not 1 <= int(numero) <= 99999999:
        raise FacturaCEnsayoError('Número de comprobante de ensayo inválido.')
    op = ET.Element(f'{{{WSFE_NS}}}FECompConsultar')
    _auth(op, token, sign, cuit)
    req = ET.SubElement(op, f'{{{WSFE_NS}}}FeCompConsReq')
    for k, v in (('CbteTipo', TIPO), ('CbteNro', numero), ('PtoVta', pv)):
        _add(req, k, v)
    return op


def leer_consulta_c(root):
    if not isinstance(root, ET.Element) or _first(root, 'Fault') is not None:
        raise FacturaCEnsayoIncierta('La consulta ARCA falló; no se reenvió ninguna factura.')
    res = _first(root, 'ResultGet')
    if res is None or not _value(res, 'CodAutorizacion'):
        return None
    return {
        'cae': _value(res, 'CodAutorizacion'),
        'vencimiento': _value(res, 'FchVto'),
        'total': _value(res, 'ImpTotal'),
        'fecha': _value(res, 'CbteFch'),
        'numero': _value(res, 'CbteNro'),
    }


def qr_url_c(cuit, pv, numero, fecha, importe, cae):
    """Codifica el enlace QR fiscal según esquema de ARCA; NO imprime tickets."""
    if not all(re.fullmatch(r'[0-9]+', str(v)) for v in (cuit, pv, numero, cae)):
        raise FacturaCEnsayoError('Faltan datos numéricos para el QR.')
    try:
        f = datetime.strptime(fecha, '%Y%m%d').strftime('%Y-%m-%d')
    except ValueError as exc:
        raise FacturaCEnsayoError('Fecha inválida para QR.') from exc
    payload = {
        'ver': 1, 'fecha': f, 'cuit': int(cuit), 'ptoVta': int(pv),
        'tipoCmp': 11, 'nroCmp': int(numero), 'importe': float(total_ensayo(importe)),
        'moneda': 'PES', 'ctz': 1, 'tipoDocRec': 99, 'nroDocRec': 0,
        'tipoCodAut': 'E', 'codAut': int(cae),
    }
    b64 = base64.b64encode(json.dumps(payload, separators=(',', ':')).encode('utf-8')).decode('ascii')
    return 'https://www.arca.gob.ar/fe/qr/?p=' + b64
