"""Consultas WSFEv1 de SOLO LECTURA para Factura C (11).

No expone FECAESolicitar, no solicita CAE ni reserva numeración.
Compatible únicamente con entorno homologación; módulo independiente del POS.
"""
from __future__ import annotations
from xml.etree import ElementTree as ET

TIPO_FACTURA_C = 11
WSFE_NS = 'http://ar.gov.afip.dif.FEV1/'

class ConsultaFacturaCError(ValueError):
    pass


def armar_ultimo_c(token, sign, cuit, punto_venta, *, entorno='homologacion'):
    if entorno != 'homologacion':
        raise ConsultaFacturaCError('Solo se permiten consultas de homologación.')
    if not token or not sign or not str(cuit).isdigit() or len(str(cuit)) != 11:
        raise ConsultaFacturaCError('Credenciales fiscales incompletas.')
    if type(punto_venta) is not int or not 1 <= punto_venta <= 99999:
        raise ConsultaFacturaCError('Punto de venta inválido.')
    root = ET.Element(f'{{{WSFE_NS}}}FECompUltimoAutorizado')
    auth = ET.SubElement(root, f'{{{WSFE_NS}}}Auth')
    for key, value in (('Token', token), ('Sign', sign), ('Cuit', cuit)):
        ET.SubElement(auth, f'{{{WSFE_NS}}}{key}').text = str(value)
    for key, value in (('PtoVta', punto_venta), ('CbteTipo', TIPO_FACTURA_C)):
        ET.SubElement(root, f'{{{WSFE_NS}}}{key}').text = str(value)
    return root


def leer_ultimo_c(root):
    if not isinstance(root, ET.Element):
        raise ConsultaFacturaCError('Respuesta XML inválida.')
    fault = next((n for n in root.iter() if n.tag.split('}')[-1] == 'Fault'), None)
    if fault is not None:
        raise ConsultaFacturaCError('ARCA respondió con un error SOAP.')
    for errors in (n for n in root.iter() if n.tag.split('}')[-1] == 'Errors'):
        if any(n.tag.split('}')[-1] == 'Err' for n in errors.iter()):
            raise ConsultaFacturaCError('ARCA rechazó la consulta de Factura C.')
    result = next((n for n in root.iter() if n.tag.split('}')[-1] == 'FECompUltimoAutorizadoResult'), None)
    if result is None:
        raise ConsultaFacturaCError('ARCA no devolvió el resultado de la consulta C.')
    value = next(((n.text or '').strip() for n in result.iter() if n.tag.split('}')[-1] == 'CbteNro'), '')
    if not value.isdigit():
        raise ConsultaFacturaCError('ARCA no devolvió una numeración válida.')
    number = int(value)
    if number < 0 or number > 99999999:
        raise ConsultaFacturaCError('Numeración fuera de rango.')
    return number
