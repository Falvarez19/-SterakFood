"""Diagnóstico NO fiscal de conectividad a WSFEv1 en homologación.

Uso actual: `views.fiscal_probar_conexion_arca`.
NO autentica, NO consulta cuentas y NO solicita CAE.
"""

from xml.etree import ElementTree as ET

import requests


class ArcaDiagnosticoError(Exception):
    """Falla técnica al consultar el estado del servicio de homologación."""


_URL_HOMOLOGACION = 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx'
_SOAP_ACTION = 'http://ar.gov.afip.dif.FEV1/FEDummy'
_XML_REQUEST = b'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:ar="http://ar.gov.afip.dif.FEV1/">
  <soap:Body><ar:FEDummy/></soap:Body>
</soap:Envelope>'''
_SOAP_NS = 'http://schemas.xmlsoap.org/soap/envelope/'
_FE_NS = 'http://ar.gov.afip.dif.FEV1/'


def fedummy_homologacion():
    """Solo prueba que los servidores de homologación respondan; no emite.

    Devuelve el contrato JSON esperado por la vista existente:
    {'disponible': bool, 'estados': {'AppServer': ..., ...}}
    """
    try:
        respuesta = requests.post(
            _URL_HOMOLOGACION,
            data=_XML_REQUEST,
            headers={
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': f'"{_SOAP_ACTION}"',
            },
            timeout=(5, 12),
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        raise ArcaDiagnosticoError(
            'No se pudo contactar con ARCA (homologación). Reintentá más tarde.'
        ) from exc

    if respuesta.status_code != 200:
        raise ArcaDiagnosticoError(
            f'ARCA homologación respondió con HTTP {respuesta.status_code}.'
        )
    if len(respuesta.content) > 100_000:
        raise ArcaDiagnosticoError('La respuesta de ARCA supera el tamaño permitido.')
    try:
        raiz = ET.fromstring(respuesta.content)
    except ET.ParseError as exc:
        raise ArcaDiagnosticoError('ARCA devolvió una respuesta XML inválida.') from exc

    body = raiz.find(f'{{{_SOAP_NS}}}Body')
    resultado = body.find(f'.//{{{_FE_NS}}}FEDummyResult') if body is not None else None
    if resultado is None:
        raise ArcaDiagnosticoError('No se encontró el resultado FEDummy en ARCA.')

    estados = {}
    for campo in ('AppServer', 'DbServer', 'AuthServer'):
        nodo = resultado.find(f'{{{_FE_NS}}}{campo}')
        if nodo is None or not (nodo.text or '').strip():
            raise ArcaDiagnosticoError('La respuesta FEDummy está incompleta.')
        estados[campo] = nodo.text.strip()[:30]

    return {
        'disponible': all(estado.upper() == 'OK' for estado in estados.values()),
        'estados': estados,
    }
