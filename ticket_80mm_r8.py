"""SterakFood: presentación de controles de mesa de 80 mm.

Solo presentación/impresión: no consulta colas, no genera ventas, no emite ARCA.
Una base común para el agente Desktop y la ticketera clásica de Windows.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import re
import textwrap

ANCHO = 40  # Fuente ESC/POS A, rollo térmico 80 mm (dependiente de la impresora).
ANCHO_PRODUCTO = 20
ANCHO_UNITARIO = 9
ANCHO_IMPORTE = 9
MARCA = 'SF_CONTROL_80_R8_3COLUMNAS'
# SF_CONTROL_80_R9_ANCHO_REAL_40: evita que precios y totales salten de línea.


def _limpio(valor):
    """Evita saltos de línea inyectados y caracteres incompatibles con CP850."""
    s = re.sub(r'\s+', ' ', str(valor or '')).strip()
    s = ''.join(c for c in s if ord(c) >= 32)
    return s.encode('cp850', errors='replace').decode('cp850')


def _numero(valor):
    if isinstance(valor, Decimal):
        return valor
    dato = _limpio(valor).replace('$', '').replace(' ', '')
    if ',' in dato and '.' in dato:
        if dato.rfind(',') > dato.rfind('.'):
            dato = dato.replace('.', '').replace(',', '.')
        else:
            dato = dato.replace(',', '')
    elif ',' in dato:
        if re.search(r',\d{1,2}$', dato):
            dato = dato.replace(',', '.')
        else:
            dato = dato.replace(',', '')
    return Decimal(dato or '0')


def _moneda(valor):
    valor = _numero(valor).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    texto = format(valor, ',.2f').replace(',', '_').replace('.', ',').replace('_', '.')
    if texto.endswith(',00'):
        texto = texto[:-3]
    return '$' + texto


def _cantidad(valor):
    d = _numero(valor)
    return str(int(d)) if d == d.to_integral_value() else format(d.normalize(), 'f')


def _envolver(texto, ancho):
    return textwrap.wrap(_limpio(texto), width=ancho, break_long_words=True,
                         break_on_hyphens=False) or ['']


def _fila_producto(cantidad, nombre, unitario, importe):
    """Columnas que siempre suman 40, sin perder dígitos por truncamiento."""
    nombre = f'{_cantidad(cantidad)}x {_limpio(nombre).upper()}'
    pu, imp = _moneda(unitario), _moneda(importe)
    if len(pu) > ANCHO_UNITARIO or len(imp) > ANCHO_IMPORTE:
        # Importes excepcionalmente grandes: mostrar completos, debajo del producto.
        return [("normal", linea) for linea in _envolver(nombre, ANCHO)] + [
            ("normal", linea) for linea in _envolver(f'UNITARIO: {pu}  IMPORTE: {imp}', ANCHO)]
    partes = _envolver(nombre, ANCHO_PRODUCTO)
    resultado = [("normal", f'{partes[0]:<{ANCHO_PRODUCTO}} {pu:>{ANCHO_UNITARIO}} {imp:>{ANCHO_IMPORTE}}')]
    resultado.extend(("normal", pedazo) for pedazo in partes[1:])
    return resultado


def preparar_lineas(mesa, mozo, detalles, total, momento=None, nombre_cliente='',
                    titulo='CONTROL DE MESA', observaciones='', pago='',
                    descuento_efectivo_finde=False):
    """Devuelve pares (estilo, línea) sin realizar operaciones sobre la BD."""
    ahora = momento or datetime.now()
    lineas = [
        ('normal', f'FECHA: {ahora:%d/%m/%Y}   HORA: {ahora:%H:%M}'),
        ('vacio', ''),
        ('titulo', _limpio(titulo)),
        ('vacio', ''),
    ]
    izq = ('MESA: ' + _limpio(mesa)) if mesa else 'PARA LLEVAR'
    der = 'MOZO: ' + _limpio(mozo) if mozo else ''
    if len(izq) + len(der) + 2 <= ANCHO:
        lineas.append(('mesa', izq + ' ' * (ANCHO - len(izq) - len(der)) + der))
    else:
        lineas.extend([('mesa', linea) for linea in _envolver(izq, ANCHO)])
        if der:
            lineas.extend([('mesa', linea) for linea in _envolver(der, ANCHO)])
    nombre_cliente = _limpio(nombre_cliente)
    if nombre_cliente and not nombre_cliente.upper().startswith('POS SALON'):
        lineas.extend([('normal', linea) for linea in _envolver('CLIENTE: ' + nombre_cliente, ANCHO)])
    lineas.append(('normal', '-' * ANCHO))
    lineas.append(('cabecera', f'{"CANT./PRODUCTO":<{ANCHO_PRODUCTO}} {"P.UNIT.":>{ANCHO_UNITARIO}} {"IMPORTE":>{ANCHO_IMPORTE}}'))
    lineas.append(('normal', '-' * ANCHO))

    for item in detalles:
        cantidad, nombre, unitario = item['cantidad'], item['nombre'], item['unitario']
        importe = item.get('importe', _numero(unitario) * _numero(cantidad))
        lineas.extend(_fila_producto(cantidad, nombre, unitario, importe))
        for opcion in item.get('opciones') or []:
            if opcion:
                lineas.extend(('detalle', linea) for linea in _envolver('  > ' + _limpio(opcion), ANCHO))
        if item.get('celiaco'):
            lineas.append(('alerta', '*** CELIACO: REVISAR ***'))
    if observaciones:
        lineas.extend(('detalle', linea) for linea in _envolver('OBS: ' + _limpio(observaciones), ANCHO))
    lineas.append(('normal', '-' * ANCHO))

    total_num = _numero(total)
    if descuento_efectivo_finde and 'EFECTIVO' in str(pago).upper() and ahora.weekday() >= 5 and 12 <= ahora.hour < 15:
        descuento = (total_num * Decimal('0.10')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        lineas.append(('normal', _par('SUBTOTAL', _moneda(total_num))))
        lineas.append(('normal', _par('DESC. 10% EFECTIVO', '-' + _moneda(descuento))))
        lineas.append(('total', _par('TOTAL A PAGAR', _moneda(total_num - descuento))))
    else:
        lineas.append(('total', _par('TOTAL', _moneda(total_num))))
    lineas.extend([('vacio', ''), ('gracias', 'GRACIAS POR ELEGIRNOS'),
                   ('aviso', 'NO VALIDO COMO FACTURA')])
    for _, linea in lineas:
        if len(linea) > ANCHO:
            raise ValueError('Linea fuera del ancho seguro de 40 columnas: ' + repr(linea))
    return lineas


def _par(izq, der):
    if len(izq) + len(der) + 1 <= ANCHO:
        return izq + ' ' * (ANCHO - len(izq) - len(der)) + der
    raise ValueError('El total es demasiado largo para mostrarlo sin recortar.')


def _raw_espos(lineas):
    """Envía ESC/POS fuente A, ancho normal y TOTAL doble alto (no doble ancho)."""
    datos = bytearray(b'\x1b@\x1bM\x00\x1b!\x00\x1d!\x00\x1b2')
    for estilo, linea in lineas:
        centrado = estilo in ('titulo', 'gracias', 'aviso')
        negrita = estilo in ('titulo', 'mesa', 'cabecera', 'total', 'gracias', 'alerta')
        doble_alto = estilo == 'total'
        datos.extend(b'\x1ba\x01' if centrado else b'\x1ba\x00')
        datos.extend(b'\x1bE\x01' if negrita else b'\x1bE\x00')
        datos.extend(b'\x1d!\x10' if doble_alto else b'\x1d!\x00')
        # Las columnas ya estan compuestas: NO colapsar espacios de alineacion.
        datos.extend((linea + '\n').encode('cp850', errors='replace'))
        if doble_alto:
            datos.extend(b'\x1d!\x00')
    datos.extend(b'\x1bE\x00\x1ba\x00\x1d!\x00\n\n\n\n\x1dV\x00')
    return bytes(datos)


def ticket_desktop_80mm(p):
    """Renderiza desde Pedido; no modifica su estado ni marca impreso."""
    from django.utils import timezone
    momento = timezone.localtime(timezone.now())
    items = []
    for detalle in p.items.select_related('producto').all():
        producto = detalle.producto
        opciones = []
        for campo in ('variante_elegida', 'guarnicion_elegida', 'punto_coccion_elegido',
                      'relleno_elegido', 'salsa_elegida', 'adicional_elegido', 'hielo_elegido'):
            val = getattr(detalle, campo, '')
            if val:
                opciones.append(val)
        items.append({
            'cantidad': detalle.cantidad,
            'nombre': getattr(producto, 'nombre', None) or 'Producto eliminado',
            'unitario': detalle.precio_unitario,
            'importe': detalle.precio_unitario * detalle.cantidad,
            'opciones': opciones,
            'celiaco': getattr(detalle, 'aviso_celiaco', False),
        })
    observaciones = ''
    if getattr(p, 'tipo_entrega', None) == 'para_llevar':
        extra = getattr(p, 'para_llevar', None)
        observaciones = getattr(extra, 'observaciones', '') if extra else ''
    plan = preparar_lineas(
        mesa=getattr(p, 'numero_mesa', ''), mozo=getattr(p, 'mozo', ''),
        detalles=items, total=p.total, momento=momento,
        nombre_cliente=getattr(p, 'nombre_cliente', ''),
        titulo=('CONTROL PARA LLEVAR' if getattr(p, 'tipo_entrega', None) == 'para_llevar' else 'CONTROL DE MESA'),
        observaciones=observaciones,
    )
    return _raw_espos(plan)


def ticket_web_80mm(impresora, pedido):
    """Control 80mm de ticketera.py antigua; conserva el descuento histórico del cobro."""
    datos = []
    for item in pedido.get('items_caja', []) or []:
        descripcion = _limpio(item.get('descripcion', ''))
        match = re.match(r'^([\d.,]+)\s*x\s*(.*)$', descripcion, flags=re.IGNORECASE)
        cant = _numero(match.group(1)) if match else Decimal('1')
        nombre = match.group(2) if match else descripcion
        if cant <= 0:
            raise ValueError('Cantidad inválida de ticket web.')
        sub = _numero(item.get('subtotal', '0'))
        datos.append({'cantidad': cant, 'nombre': nombre, 'unitario': sub / cant, 'importe': sub})
    momento = datetime.now()
    entrega = str(pedido.get('entrega', '')).lower()
    titulo = 'CONTROL PARA LLEVAR' if entrega == 'para_llevar' else 'CONTROL DE MESA'
    plan = preparar_lineas(
        mesa=pedido.get('mesa', ''), mozo=pedido.get('mozo') or 'CAJA',
        detalles=datos, total=pedido.get('total', 0), momento=momento,
        titulo=titulo, pago=pedido.get('pago', ''), descuento_efectivo_finde=True,
    )
    # Python-escpos: utiliza su API de texto, sin tocar impresiones fiscales.
    impresora.text('\x1b\x40')
    for estilo, linea in plan:
        impresora.set(
            align='center' if estilo in ('titulo','gracias','aviso') else 'left',
            font='a',
            bold=estilo in ('titulo','mesa','cabecera','total','gracias','alerta'),
            double_height=(estilo == 'total'), double_width=False,
        )
        impresora.text(linea + '\n')
    impresora.text('\n\n\n\n')
    impresora.cut()
