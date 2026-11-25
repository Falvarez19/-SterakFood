"""Agente de comandas Windows/LAN; usa únicamente SQLite local.

No consume APIs HTTP ni emite comprobantes ARCA. Un envío con resultado incierto
NO se repite automáticamente: el operador debe comprobar la impresora primero.
"""
from __future__ import annotations
import re
import socket
import textwrap
from django.db import transaction
from django.utils import timezone
from pedidos.models import Pedido, ImpresionComprobanteCuenta, ConfiguracionImpresorasPOS
from .models import ImpresionLocal6D, AjustesDesktop6D

MAX_BATCH = 20


def _texto(value):
    s = str(value or '').replace('\r', ' ').replace('\n',' ')
    return ''.join(c if ord(c) >= 32 else ' ' for c in s)[:200]


def _sin_importes(value):
    # Cocina y barra NO deben ver precios, ni suplementos dentro de variantes.
    return re.sub(r'\s*\(\s*[+-]\s*\$?\s*\d+(?:[.,]\d{1,2})?\s*\)', '', _texto(value))


def _raw(lines):
    contenido = '\n'.join(_texto(x) for x in lines) + '\n\n\n'
    return b'\x1b@' + contenido.encode('cp850', errors='replace') + b'\x1dV\x00'


def _pedido_bytes(p, destino):
    if destino != 'caja' and p.tipo_entrega != 'para_llevar':
        raise ValueError('Salón manual no envía comandas a cocina.')
    titulo = 'CONTROL DE MESA - NO FISCAL' if destino == 'caja' else 'COMANDA PARA LLEVAR'
    lines = [titulo, 'PEDIDO #' + str(p.pk)]
    if p.numero_mesa: lines.append('MESA ' + _texto(p.numero_mesa))
    if p.mozo: lines.append('MOZO: ' + _texto(p.mozo))
    if p.nombre_cliente: lines.append('CLIENTE: ' + _texto(p.nombre_cliente))
    lines.append('-'*32)
    for d in p.items.select_related('producto').all():
        nombre = _texto(d.producto.nombre if d.producto else 'Producto eliminado')
        lines.extend(textwrap.wrap(f'{d.cantidad}x {nombre}', width=32))
        for campo in ('variante_elegida','guarnicion_elegida','punto_coccion_elegido',
                      'relleno_elegido','salsa_elegida','adicional_elegido','hielo_elegido'):
            val = getattr(d,campo,'')
            if val:
                item = (_texto(val) if destino=='caja' else _sin_importes(val))
                lines.extend(textwrap.wrap(' > '+item,width=32))
        if d.aviso_celiaco:
            lines.append('*** CELIACO: REVISAR ***')
        if destino == 'caja':
            lines.append('$ '+str(d.precio_unitario * d.cantidad))
    if p.tipo_entrega == 'para_llevar':
        extra = getattr(p,'para_llevar',None)
        if extra and extra.observaciones:
            lines.append('OBS: '+_texto(extra.observaciones))
    lines.append('-'*32)
    if destino == 'caja':
        lines.extend(['TOTAL $ '+str(p.total),'NO VALIDO COMO FACTURA'])
    return _raw(lines)


def _cuenta_bytes(job):
    c = job.comprobante
    lines = ['CUENTA CORRIENTE - NO FISCAL',_texto(c.cliente_nombre),
             'COMPROBANTE #'+str(c.pk), '-'*32]
    for item in c.items or []:
        if not isinstance(item,dict): continue
        lines.extend(textwrap.wrap(_texto(item.get('nombre','Consumo')),width=32))
        lines.append('$ '+_texto(item.get('subtotal','0')))
    lines.extend(['-'*32,'TOTAL $ '+str(c.total),'SALDO $ '+str(c.saldo_posterior),
                  'NO VALIDO COMO FACTURA'])
    return _raw(lines)


def _send_network(ip, data):
    # Fallo al conectar es reintentable; una vez iniciada la escritura es incierto.
    try:
        client = socket.create_connection((ip, 9100),timeout=3)
    except OSError as exc:
        raise PrinterNotReady('Impresora de red no disponible: ' + str(exc)) from exc
    with client:
        try:
            client.settimeout(5)
            client.sendall(data)
        except Exception as exc:
            raise UncertainPrintError(str(exc)) from exc


def _send_windows(printer_name, data):
    try:
        import win32print
    except ImportError as exc:
        raise PrinterNotReady('Falta pywin32 para la impresora USB Windows.') from exc
    try:
        p = win32print.OpenPrinter(printer_name)
    except Exception as exc:
        raise PrinterNotReady('No se pudo abrir la impresora de caja: ' + str(exc)) from exc
    started = False
    try:
        win32print.StartDocPrinter(p, 1, ('SterakFood - ticket no fiscal',None,'RAW'))
        started = True
        try:
            win32print.StartPagePrinter(p)
            win32print.WritePrinter(p,data)
            win32print.EndPagePrinter(p)
            win32print.EndDocPrinter(p)
        except Exception as exc:
            raise UncertainPrintError(str(exc)) from exc
    finally:
        if started:
            try: win32print.ClosePrinter(p)
            except Exception: pass
        else: win32print.ClosePrinter(p)


class PrinterNotReady(Exception): pass
class UncertainPrintError(Exception): pass


def _descubrir_trabajos():
    """Idempotencia de trabajos, sin marcar ventas como impresas de antemano."""
    pids = (Pedido.objects.filter(impreso_caja=False)
            .filter(tipo_pago='ticket_salon_temporal')
            .order_by('pk')[:MAX_BATCH])
    for p in pids:
        ImpresionLocal6D.objects.get_or_create(tipo='pedido', referencia_id=p.pk,destino='caja')
    llevados = (Pedido.objects.filter(impreso_caja=False,tipo_entrega='para_llevar')
                .exclude(estado='cancelado').order_by('pk')[:MAX_BATCH])
    for p in llevados:
        ImpresionLocal6D.objects.get_or_create(tipo='pedido', referencia_id=p.pk,destino='cocina')
    ccs = ImpresionComprobanteCuenta.objects.filter(impreso=False).order_by('pk')[:MAX_BATCH]
    for cc in ccs:
        ImpresionLocal6D.objects.get_or_create(tipo='cuenta',referencia_id=cc.pk,destino='caja')


def _finalizar_referencia(reg):
    if reg.estado != 'enviado': return
    if ImpresionLocal6D.objects.filter(tipo=reg.tipo,referencia_id=reg.referencia_id).exclude(estado='enviado').exists():
        return
    if reg.tipo == 'pedido':
        Pedido.objects.filter(pk=reg.referencia_id).update(impreso_caja=True)
    else:
        ImpresionComprobanteCuenta.objects.filter(pk=reg.referencia_id).update(impreso=True,fecha_impreso=timezone.now())


def procesar_una(reg, config):
    # La asignación 'enviando' es duradera ANTES de cualquier efecto físico.
    with transaction.atomic():
        actualizado = ImpresionLocal6D.objects.filter(pk=reg.pk,estado='pendiente').update(estado='enviando',intentos=reg.intentos+1)
        if not actualizado: return
    try:
        if reg.tipo=='pedido':
            pedido = Pedido.objects.prefetch_related('items__producto').filter(pk=reg.referencia_id).first()
            if pedido is None:
                raise PrinterNotReady('Pedido no encontrado: requiere revisión manual.')
            datos = _pedido_bytes(pedido,reg.destino)
        elif reg.tipo=='cuenta':
            registro = ImpresionComprobanteCuenta.objects.select_related('comprobante').filter(pk=reg.referencia_id).first()
            if registro is None:
                raise PrinterNotReady('Comprobante no encontrado: requiere revisión manual.')
            datos = _cuenta_bytes(registro)
        else: raise ValueError('Tipo de trabajo no permitido.')
        if reg.destino == 'caja':
            _send_windows(config.caja_windows,datos)
        elif reg.destino == 'cocina':
            _send_network(config.ip_cocina,datos)
        elif reg.destino == 'barra':
            _send_network(config.ip_barra,datos)
        else: raise ValueError('Destino desconocido.')
    except PrinterNotReady as exc:
        # No se imprimió nada: el trabajo queda pendiente para reintentar.
        ImpresionLocal6D.objects.filter(pk=reg.pk).update(estado='pendiente',ultimo_error=str(exc)[:400])
        return
    except (OSError,UncertainPrintError,ValueError) as exc:
        # Podría haber llegado parte o todo el ticket: nunca reintentar solo.
        ImpresionLocal6D.objects.filter(pk=reg.pk).update(estado='incierto',ultimo_error=str(exc)[:400])
        return
    ImpresionLocal6D.objects.filter(pk=reg.pk).update(estado='enviado',ultimo_error='')
    reg.estado = 'enviado'
    _finalizar_referencia(reg)


def iteracion():
    ajuste = AjustesDesktop6D.objects.filter(pk=1).first()
    if not ajuste or not ajuste.impresion_activa: return
    config = ConfiguracionImpresorasPOS.objects.filter(pk=1).first()
    if not config: return
    _descubrir_trabajos()
    # Si se reinició el proceso mientras 'enviando', la impresión es incierta.
    ImpresionLocal6D.objects.filter(estado='enviando').update(
        estado='incierto', ultimo_error='El agente se cerró durante el envío. Verificar ticket antes de repetir.')
    for reg in ImpresionLocal6D.objects.filter(estado='pendiente').order_by('pk')[:MAX_BATCH]:
        procesar_una(reg,config)
