"""Captura por cambios reales de SQLite: no toca la caja ni emitie facturas."""
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from .models import Desktop6eOutbox
from .protocol import TIPOS, sha


def solo_local():
    return bool(getattr(settings,'STERAK_DESKTOP_MODE',False))


def encolar(tipo, origen, payload):
    if not solo_local() or tipo not in TIPOS:
        return
    cuerpo={'tipo':tipo,'origen':origen,**payload}
    # Se preserva el primer snapshot confirmado para que un reintento no altere el evento.
    Desktop6eOutbox.objects.get_or_create(
        tipo=tipo, origen=origen,
        defaults={'payload':cuerpo,'digest':sha(cuerpo)},
    )


def _detalle(p):
    # Snapshot de nombres/precios: nunca depender de IDs locales del servidor.
    from pedidos.models import DetallePedido
    result=[]
    for d in DetallePedido.objects.filter(pedido_id=p.pk).select_related('producto').order_by('pk'):
        result.append({'nombre':(d.producto.nombre if d.producto else 'Producto eliminado')[:200],
                       'codigo':str(d.producto.codigo_rapido or '') if d.producto else '',
                       'cantidad':int(d.cantidad),'unitario':str(d.precio_unitario),
                       'celiaco':bool(d.aviso_celiaco)})
    return result


def capturar_pedido(pk):
    if not solo_local(): return
    from pedidos.models import Pedido, PedidoParaLlevar
    p=Pedido.objects.filter(pk=pk).first()
    if not p or p.estado=='cancelado': return
    if p.tipo_entrega=='mesa' and (p.nombre_cliente or '').startswith('POS SALON'):
        if p.estado not in ('listo','entregado') or p.tipo_pago not in ('efectivo','debito','mercadopago','cuenta_corriente'):
            return
        if p.total is None or Decimal(p.total)<=0:return
        encolar('venta.salon',f'pedido:{p.pk}',{
            'local_id':p.pk,'total':str(p.total),'medio':p.tipo_pago,
            'mesa':str(p.numero_mesa or '')[:10],'mozo':str(p.mozo or '')[:100],
            'fecha':p.fecha_creacion.isoformat(),'items':_detalle(p),
            'cuenta_corriente':p.tipo_pago=='cuenta_corriente',
        })
    if p.tipo_entrega!='para_llevar': return
    try: extra=PedidoParaLlevar.objects.get(pedido_id=pk)
    except PedidoParaLlevar.DoesNotExist:return
    capturar_para_llevar(extra.pk)
    if p.tipo_pago in ('efectivo','debito','mercadopago') and p.total and p.total>0:
        encolar('cobro.para_llevar',f'pedido:{p.pk}',{
            'pedido_local_id':p.pk,'solicitud_id':str(extra.solicitud_id),
            'total':str(p.total),'medio':p.tipo_pago,
            'fecha_cobro':extra.fecha_cobro.isoformat() if extra.fecha_cobro else '',
        })


def capturar_para_llevar(pk):
    if not solo_local():return
    from pedidos.models import PedidoParaLlevar
    extra=PedidoParaLlevar.objects.select_related('pedido').filter(pk=pk).first()
    if not extra:return
    p=extra.pedido
    encolar('pedido.para_llevar',f'pedido:{p.pk}',{
        'pedido_local_id':p.pk,'solicitud_id':str(extra.solicitud_id),
        'fecha':p.fecha_creacion.isoformat(),'total':str(p.total),
        'cliente':str(p.nombre_cliente or '')[:100],
        'observaciones':str(extra.observaciones or '')[:600],
        'estado_inicial':p.estado,'items':_detalle(p),
    })


def capturar_cuenta(pk):
    if not solo_local():return
    from pedidos.models import CuentaCorriente
    obj=CuentaCorriente.objects.filter(pk=pk).first()
    if not obj:return
    # Cada revisión de datos genera un evento diferente, pero reintentos no duplican.
    import hashlib
    from .protocol import canonical
    info={'local_id':obj.pk,'nombre':obj.nombre[:120],
          'telefono':obj.telefono[:30],'nota':obj.nota[:500],
          'activa':bool(obj.activa),'fecha':obj.fecha_actualizacion.isoformat()}
    revision=hashlib.sha256(canonical(info)).hexdigest()[:16]
    encolar('cuenta.estado',f'cuenta:{pk}:{revision}',info)


def capturar_movimiento(pk):
    if not solo_local():return
    from pedidos.models import MovimientoCuentaCorriente
    mov=MovimientoCuentaCorriente.objects.select_related('cuenta').filter(pk=pk).first()
    if not mov:return
    encolar('cuenta.movimiento',f'movimiento:{pk}',{
        'local_id':mov.pk,'cuenta_local_id':mov.cuenta_id,
        'cuenta_nombre':mov.cuenta.nombre[:120],
        'tipo_movimiento':mov.tipo,'total':str(abs(mov.monto)),
        'monto_firmado':str(mov.monto),
        'descripcion':mov.descripcion[:180],
        'fecha':mov.fecha.isoformat(),
        'operacion_id':str(mov.operacion_id or '')[:64],
    })


def capturar_corte(pk):
    if not solo_local():return
    from pedidos.models import CorteHistorialVentas
    corte=CorteHistorialVentas.objects.filter(pk=pk).first()
    if not corte:return
    encolar('caja.corte',f'corte:{pk}',{
        'local_id':pk,'fecha':corte.fecha.isoformat(),
        'cantidad_pedidos':corte.cantidad_pedidos,
        'total':str(corte.total_archivado),'origen_corte':corte.origen,
    })
