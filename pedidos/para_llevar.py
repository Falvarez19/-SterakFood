"""Módulo POS reutilizable para llevar; no genera facturas fiscales.

Crea pedidos de mostrador sin número de mesa, y los publica en la cola
existente de la ticketera. Los pagos pendientes no son ventas cobradas.
"""
import json
import re
import uuid
from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import Configuracion, DetallePedido, Pedido, PedidoParaLlevar, Producto, PuntoVenta

PAGOS = ('efectivo', 'debito', 'mercadopago')
SIN_COBRAR = 'pendiente_para_llevar'

# Misma fuente de productos/opciones del menú público; jamás duplicamos un menú.
# "adicional" permite varias elecciones; el resto requiere una selección cuando
# el comercio configuró opciones en el producto.
OPCIONES = (
    ('variante', 'variantes', 'variante_elegida'),
    ('guarnicion', 'guarniciones', 'guarnicion_elegida'),
    ('punto', 'puntos_coccion', 'punto_coccion_elegido'),
    ('relleno', 'rellenos', 'relleno_elegido'),
    ('salsa', 'salsas', 'salsa_elegida'),
    ('hielo', 'opcion_hielo', 'hielo_elegido'),
    ('adicional', 'adicionales', 'adicional_elegido'),
)
AJUSTE_PRECIO = re.compile(r'\(([+-])(\d+(?:\.\d+)?)\)')


def _opciones_producto(producto):
    return {
        clave: [v.strip() for v in (getattr(producto, campo) or '').split(',') if v.strip()]
        for clave, campo, _ in OPCIONES
    }


def _catalogo_publico():
    """Productos del menú que ve el cliente, nunca exclusivos de Salón.

    Cuando hay puntos de venta abiertos, solo los productos publicados en
    alguno de ellos pueden venderse para llevar. Si no hay puntos configurados,
    mantenemos el modo general del menú público.
    """
    productos = Producto.objects.filter(disponible=True).exclude(
        categoria__nombre='Salon'
    ).select_related('categoria').order_by('categoria__nombre', 'orden', 'nombre')
    abiertos = PuntoVenta.objects.filter(abierto=True)
    if PuntoVenta.objects.exists():
        productos = productos.filter(puntos_venta__in=abiertos).distinct()
    return productos


def _serializar_catalogo(producto):
    return {
        'id': producto.pk, 'nombre': producto.nombre,
        'codigo': producto.codigo_rapido or str(producto.pk),
        'categoria': producto.categoria.nombre,
        'precio': str(producto.precio),
        'imagen': producto.imagen.url if producto.imagen else '',
        'opciones': _opciones_producto(producto),
    }


def _validar_opciones(producto, raw):
    if not isinstance(raw, dict):
        raise ValueError('Las opciones del producto son inválidas.')
    if set(raw) - {c for c, _, _ in OPCIONES}:
        raise ValueError('Hay opciones que no pertenecen al menú.')
    disponibles = _opciones_producto(producto)
    eleccion = {}
    ajuste = Decimal('0.00')
    for clave, _, columna in OPCIONES:
        opciones = disponibles[clave]
        valor = raw.get(clave, [] if clave == 'adicional' else '')
        if clave == 'adicional':
            if not isinstance(valor, list) or len(valor) > len(opciones):
                raise ValueError('Los adicionales seleccionados no son válidos.')
            valores = [str(v) for v in valor]
            if len(set(valores)) != len(valores) or any(v not in opciones for v in valores):
                raise ValueError('Elegiste un adicional que no figura en el menú.')
            texto = ' + '.join(valores)
        else:
            if not isinstance(valor, str):
                raise ValueError('Las opciones seleccionadas no son válidas.')
            texto = valor
            if (opciones and texto not in opciones) or (not opciones and texto):
                raise ValueError(f'Elegí una opción válida de {clave} para {producto.nombre}.')
            valores = [texto] if texto else []
        if len(texto) > 100:  # coincide con los campos de DetallePedido
            raise ValueError('Las opciones elegidas son demasiado largas.')
        eleccion[columna] = texto
        for elegido in valores:
            for signo, importe in AJUSTE_PRECIO.findall(elegido):
                diferencia = Decimal(importe)
                ajuste += diferencia if signo == '+' else -diferencia
    precio_final = producto.precio + ajuste
    if not Decimal('0.00') < precio_final <= Decimal('99999999.99'):
        raise ValueError('El precio con las opciones seleccionadas no es válido.')
    return eleccion, precio_final


def _autorizado(request):
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status': 'error', 'mensaje': 'Iniciá sesión en el POS.'}, status=403)
    config = Configuracion.objects.filter(pk=1).first()
    if config and not config.salon_habilitado:
        return JsonResponse({'status': 'error', 'mensaje': 'El POS está desactivado.'}, status=403)
    return None


def _leer_json(request):
    try:
        value = json.loads(request.body.decode('utf-8'))
        if not isinstance(value, dict):
            raise ValueError('Se esperaba un objeto.')
        return value
    except (UnicodeError, ValueError, TypeError):
        return None


def _serialize(p):
    return {
        'id': p.id,
        'cliente': p.nombre_cliente or 'Cliente sin nombre',
        'telefono': p.telefono_cliente or '',
        'notas': p.para_llevar.observaciones,
        'aviso_celiaco': any(i.aviso_celiaco for i in p.items.all()),
        'total': str(p.total),
        'estado': p.estado,
        'cobrado': p.tipo_pago != SIN_COBRAR,
        'pago': p.tipo_pago,
        'impreso': p.impreso_caja,
        'hora': timezone.localtime(p.fecha_creacion).strftime('%d/%m %H:%M'),
    }


@require_http_methods(['GET', 'POST'])
def pedidos_para_llevar(request):
    acceso = _autorizado(request)
    if acceso is not None:
        return acceso
    if request.method == 'GET':
        recientes = timezone.now() - timedelta(days=1)
        qs = (Pedido.objects.filter(tipo_entrega='para_llevar', para_llevar__isnull=False)
              .filter(Q(tipo_pago=SIN_COBRAR) | Q(fecha_creacion__gte=recientes))
              .select_related('para_llevar').prefetch_related('items').order_by('-id')[:60])
        return JsonResponse({'status': 'ok', 'pedidos': [_serialize(p) for p in qs],
                             'catalogo': [_serializar_catalogo(p) for p in _catalogo_publico()]})

    data = _leer_json(request)
    if data is None:
        return JsonResponse({'status': 'error', 'mensaje': 'Datos inválidos.'}, status=400)
    try:
        solicitud = uuid.UUID(str(data.get('solicitud_id', '')))
    except (ValueError, TypeError, AttributeError):
        return JsonResponse({'status': 'error', 'mensaje': 'Falta identificador de operación.'}, status=400)
    previa = PedidoParaLlevar.objects.filter(solicitud_id=solicitud).select_related('pedido').first()
    if previa:
        return JsonResponse({'status': 'ok', 'pedido_id': previa.pedido_id,
                             'mensaje': 'Este pedido ya estaba guardado. No se duplicó.', 'duplicado': True})

    items = data.get('items')
    if not isinstance(items, list) or not 1 <= len(items) <= 50:
        return JsonResponse({'status': 'error', 'mensaje': 'Agregá entre 1 y 50 productos.'}, status=400)
    # Cada combinación elegida es una línea diferente: milanesa común y
    # napolitana no deben fusionarse ni perder sus preferencias al imprimir.
    productos_publicos = {p.pk: p for p in _catalogo_publico()}
    lineas = {}
    try:
        for fila in items:
            if not isinstance(fila, dict):
                raise ValueError('Producto inválido.')
            producto_id = int(fila.get('producto_id'))
            cantidad = int(fila.get('cantidad'))
            if producto_id < 1 or not 1 <= cantidad <= 99:
                raise ValueError('Cantidad inválida.')
            producto = productos_publicos.get(producto_id)
            if producto is None:
                return JsonResponse({'status': 'error', 'mensaje': 'Un producto no figura disponible en el menú público.'}, status=409)
            elegidas, precio = _validar_opciones(producto, fila.get('opciones', {}))
            # Bandera estrictamente booleana. No se toma de descripciones libres.
            aviso_celiaco = fila.get('aviso_celiaco', False)
            if type(aviso_celiaco) is not bool:
                raise ValueError('La indicación para celíaco no es válida.')
            clave = (producto_id, tuple(elegidas[c] for _, _, c in OPCIONES), aviso_celiaco)
            if clave in lineas:
                lineas[clave]['cantidad'] += cantidad
            else:
                lineas[clave] = {'producto': producto, 'cantidad': cantidad,
                                'opciones': elegidas, 'precio': precio,
                                'aviso_celiaco': aviso_celiaco}
            if lineas[clave]['cantidad'] > 99:
                raise ValueError('Cantidad máxima de 99 por combinación.')
    except (TypeError, ValueError, OverflowError) as error:
        return JsonResponse({'status': 'error', 'mensaje': str(error) or 'Opciones inválidas.'}, status=400)

    total = sum((linea['precio'] * linea['cantidad'] for linea in lineas.values()), Decimal('0.00'))
    if not Decimal('0') < total <= Decimal('99999999.99'):
        return JsonResponse({'status': 'error', 'mensaje': 'El importe del pedido no es válido.'}, status=400)
    pago = str(data.get('pago') or 'pendiente').strip().lower()
    if pago not in (*PAGOS, 'pendiente'):
        return JsonResponse({'status': 'error', 'mensaje': 'Medio de pago inválido.'}, status=400)
    if pago == 'pendiente':
        pago = SIN_COBRAR
    nombre = str(data.get('cliente') or '').strip()[:100] or 'Cliente para llevar'
    telefono = str(data.get('telefono') or '').strip()[:20]
    notas = str(data.get('notas') or '').strip()[:350]

    try:
        with transaction.atomic():
            pedido = Pedido.objects.create(
                estado='preparacion', tipo_entrega='para_llevar', tipo_pago=pago,
                nombre_cliente=nombre, telefono_cliente=telefono, total=total,
                punto_venta=None, numero_mesa=None, impreso_caja=False,
            )
            PedidoParaLlevar.objects.create(
                pedido=pedido, solicitud_id=solicitud, observaciones=notas,
                fecha_cobro=timezone.now() if pago != SIN_COBRAR else None,
            )
            DetallePedido.objects.bulk_create([
                DetallePedido(
                    pedido=pedido, producto=linea['producto'],
                    cantidad=linea['cantidad'], precio_unitario=linea['precio'],
                    aviso_celiaco=linea['aviso_celiaco'], **linea['opciones'],
                )
                for linea in lineas.values()
            ])
    except IntegrityError:
        previa = PedidoParaLlevar.objects.filter(solicitud_id=solicitud).first()
        if previa:
            return JsonResponse({'status': 'ok', 'pedido_id': previa.pedido_id,
                                 'mensaje': 'Pedido ya creado. No se duplicó.', 'duplicado': True})
        raise

    return JsonResponse({'status': 'ok', 'pedido_id': pedido.id,
                         'mensaje': 'Pedido enviado a la cola de cocina.', 'duplicado': False}, status=201)


@require_http_methods(['POST'])
def cobrar_para_llevar(request, pedido_id):
    acceso = _autorizado(request)
    if acceso is not None:
        return acceso
    data = _leer_json(request)
    medio = str((data or {}).get('pago') or '').strip().lower()
    if medio not in PAGOS:
        return JsonResponse({'status': 'error', 'mensaje': 'Elegí efectivo, débito o Mercado Pago.'}, status=400)
    with transaction.atomic():
        pedido = (Pedido.objects.select_for_update()
                  .filter(pk=pedido_id, tipo_entrega='para_llevar', para_llevar__isnull=False)
                  .first())
        if not pedido:
            return JsonResponse({'status': 'error', 'mensaje': 'Pedido no encontrado.'}, status=404)
        if pedido.estado == 'cancelado':
            return JsonResponse({'status': 'error', 'mensaje': 'Pedido cancelado.'}, status=409)
        if pedido.tipo_pago != SIN_COBRAR:
            return JsonResponse({'status': 'error', 'mensaje': 'El pedido ya está cobrado.'}, status=409)
        pedido.tipo_pago = medio
        pedido.save(update_fields=['tipo_pago'])
        PedidoParaLlevar.objects.filter(pedido=pedido).update(fecha_cobro=timezone.now())
    # Registrar el cobro no vuelve a imprimir la comanda ni emite un CAE.
    return JsonResponse({'status': 'ok', 'mensaje': 'Cobro registrado. No se emitió factura automáticamente.'})


@require_http_methods(['POST'])
def estado_para_llevar(request, pedido_id):
    acceso = _autorizado(request)
    if acceso is not None:
        return acceso
    data = _leer_json(request)
    estado = str((data or {}).get('estado') or '').lower()
    if estado not in ('listo', 'entregado'):
        return JsonResponse({'status': 'error', 'mensaje': 'Estado no permitido.'}, status=400)
    with transaction.atomic():
        pedido = (Pedido.objects.select_for_update()
                  .filter(pk=pedido_id, tipo_entrega='para_llevar', para_llevar__isnull=False)
                  .first())
        if not pedido:
            return JsonResponse({'status': 'error', 'mensaje': 'Pedido no encontrado.'}, status=404)
        if pedido.estado in ('cancelado', 'entregado'):
            return JsonResponse({'status': 'error', 'mensaje': 'Pedido cerrado.'}, status=409)
        if estado == 'entregado' and pedido.tipo_pago == SIN_COBRAR:
            return JsonResponse({'status': 'error', 'mensaje': 'Primero registrá el cobro.'}, status=409)
        if estado == 'entregado' and not pedido.impreso_caja:
            return JsonResponse({'status': 'error', 'mensaje': 'La comanda sigue pendiente de impresión en cocina.'}, status=409)
        pedido.estado = estado
        pedido.save(update_fields=['estado'])
    return JsonResponse({'status': 'ok', 'mensaje': 'Estado actualizado.'})
