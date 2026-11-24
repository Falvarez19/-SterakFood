"""Preparación de Factura C para consumidores finales, SIN emisión fiscal.

Usar solo para construir/validar una vista previa. No obtiene TA, no contacta
ARCA, no reserva números, no guarda registros y no solicita CAE.
Factura C (código 11) de monotributistas: total sin desglose separado de IVA.
La emisión real requiere un motor transaccional, receptor y homologación.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from xml.etree import ElementTree as ET

WSFE_NS = 'http://ar.gov.afip.dif.FEV1/'
TIPO_FACTURA_C = 11


class SimulacionCError(ValueError):
    pass


@dataclass(frozen=True)
class FacturaCSimulada:
    tipo_comprobante: int
    punto_venta: int
    numero_ejemplo: int
    fecha: str
    importe_total: Decimal
    importe_neto: Decimal
    importe_iva: Decimal
    documento_tipo: int
    documento_numero: int
    condicion_iva_receptor: int
    moneda: str = 'PES'


def _total_decimal(value):
    text = str(value).strip()
    if not re.fullmatch(r'\d{1,8}(?:[.,]\d{1,2})?', text):
        raise SimulacionCError('Ingresá un importe positivo con hasta dos decimales.')
    try:
        total = Decimal(text.replace(',', '.')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise SimulacionCError('Importe no válido.') from exc
    if not Decimal('0.00') < total <= Decimal('99999999.99'):
        raise SimulacionCError('Importe fuera del rango del simulador.')
    return total


def preparar_ejemplo_c(total='1000.00', *, punto_venta=1, numero=1, fecha=None):
    """Construye datos simulados para una factura C a consumidor final.

    DocTipo 99 y DocNro 0 son solamente datos ficticios del ejemplo; NO
    representan autorización fiscal ni garantizan que correspondan a una
    operación real. Para producción habrá validaciones de receptor/umbrales.
    """
    if type(punto_venta) is not int or not 1 <= punto_venta <= 99999:
        raise SimulacionCError('Punto de venta de prueba inválido.')
    if type(numero) is not int or not 1 <= numero <= 99999999:
        raise SimulacionCError('Número de ejemplo inválido.')
    fecha = fecha or datetime.now().strftime('%Y%m%d')
    if not re.fullmatch(r'\d{8}', fecha):
        raise SimulacionCError('Fecha inválida.')
    try:
        datetime.strptime(fecha, '%Y%m%d')
    except ValueError as exc:
        raise SimulacionCError('Fecha inválida.') from exc
    importe = _total_decimal(total)
    return FacturaCSimulada(
        tipo_comprobante=TIPO_FACTURA_C,
        punto_venta=punto_venta,
        numero_ejemplo=numero,
        fecha=fecha,
        importe_total=importe,
        importe_neto=importe,
        importe_iva=Decimal('0.00'),
        documento_tipo=99,
        documento_numero=0,
        condicion_iva_receptor=5,
    )


def preparar_nodo_wsfe_c(datos):
    """Nodo SOAP de ejemplo sin Auth, Token ni Sign. No conecta con ARCA.

    Solo verifica campos/estructura y no debe utilizarse para una operación
    fiscal real sin completar las validaciones fiscales y de destinatario.
    """
    if not isinstance(datos, FacturaCSimulada) or datos.tipo_comprobante != TIPO_FACTURA_C:
        raise SimulacionCError('Se esperaba una simulación válida de Factura C.')
    def add(parent, key, value):
        e = ET.SubElement(parent, f'{{{WSFE_NS}}}{key}')
        e.text = str(value)
        return e
    operation = ET.Element(f'{{{WSFE_NS}}}FECAESolicitar')
    req = ET.SubElement(operation, f'{{{WSFE_NS}}}FeCAEReq')
    cab = ET.SubElement(req, f'{{{WSFE_NS}}}FeCabReq')
    for k, v in (('CantReg', 1), ('PtoVta', datos.punto_venta),
                 ('CbteTipo', 11)):
        add(cab, k, v)
    details = ET.SubElement(req, f'{{{WSFE_NS}}}FeDetReq')
    item = ET.SubElement(details, f'{{{WSFE_NS}}}FECAEDetRequest')
    values = (
        ('Concepto', 1), ('DocTipo', datos.documento_tipo),
        ('DocNro', datos.documento_numero), ('CbteDesde', datos.numero_ejemplo),
        ('CbteHasta', datos.numero_ejemplo), ('CbteFch', datos.fecha),
        ('ImpTotal', datos.importe_total), ('ImpTotConc', '0.00'),
        ('ImpNeto', datos.importe_neto), ('ImpOpEx', '0.00'),
        ('ImpTrib', '0.00'), ('ImpIVA', datos.importe_iva),
        ('MonId', datos.moneda), ('MonCotiz', 1),
        ('CondicionIVAReceptorId', datos.condicion_iva_receptor),
    )
    for k, v in values:
        add(item, k, v)
    # A diferencia de B: no se agrega un nodo Iva/AlicIva.
    return operation
