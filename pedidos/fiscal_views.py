from django.conf import settings
"""Facturación manual con *, nunca automática por medio de pago.

Sin certificado/habilitación el endpoint NO emite; sin autorización no imprime.
"""
import json
import os
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from .models import BorradorFiscal, ConfiguracionFiscal, FacturaFiscal, Producto, DetallePedido
from .arca_wsfe import (ArcaError, ArcaIncierto, _environment,
                        ultimo_autorizado, emitir_factura_b, consultar, url_qr)


def _login(request):
    return bool(request.session.get('dashboard_auth'))


def _serialize(f):
    return {'status':'ok' if f.estado == 'autorizada' else 'aviso',
            'factura_id':f.pk,'estado':f.estado,'entorno':f.entorno,
            'numero': f'{f.punto_venta:05d}-{f.numero:08d}' if f.numero else None,
            'cae':f.cae if f.estado=='autorizada' else None,
            'mensaje': 'Factura autorizada. En cola de impresión.' if f.estado=='autorizada' else f.observaciones[:250]}


def _validar_borrador(b):
    """Verificación básica de importes contra catálogo/órdenes del servidor.

    NO valida condiciones impositivas especiales; por eso se solicita confirmación
    expresa de que todos los productos están gravados al 21%.
    """
    total = Decimal('0.00')
    if not b.items or len(b.items)>150:
        raise ArcaError('Borrador sin productos válidos.')
    for item in b.items:
        cant = int(item['cantidad']); precio = Decimal(item['precio'])
        if cant < 1 or cant > 1000 or precio < 0 or precio.as_tuple().exponent < -2:
            raise ArcaError('Cantidad o precio inválidos.')
        product_id = int(item.get('producto_id') or 0)
        if not product_id: raise ArcaError('Producto sin ID; no se puede emitir.')
        producto = Producto.objects.filter(pk=product_id).first()
        if not producto: raise ArcaError('Hay un producto eliminado. Revisar la mesa.')
        # Productos POS: precio de catálogo debe coincidir. Para web, usar precio
        # efectivamente almacenado en DetallePedido y confirmar que pertenece a mesa.
        detalle = int(item.get('detalle_id') or 0)
        if detalle:
            d = DetallePedido.objects.select_related('pedido').filter(pk=detalle, producto_id=product_id).first()
            if not d or (str(d.pedido.numero_mesa or '') != str(b.mesa)) or d.cantidad < cant or d.precio_unitario != precio:
                raise ArcaError('El pedido web cambió. Refrescá la mesa antes de facturar.')
        elif Decimal(producto.precio) != precio:
            raise ArcaError(f'El precio de {producto.nombre} cambió; revisá la mesa antes de facturar.')
        total += precio*cant
    total=total.quantize(Decimal('.01'))
    if total <= 0 or total != b.total_estimado:
        raise ArcaError('El total no coincide con el borrador.')
    return total


@require_POST
def emitir_manual(request):
    if not _login(request): return JsonResponse({'status':'error','mensaje':'No autorizado.'},status=403)
    try:
        data=json.loads(request.body.decode('utf-8'))
        if data.get('confirmacion') != 'FACTURAR_CON_ASTERISCO':
            raise ArcaError('Falta confirmación manual de facturación.')
        if data.get('iva_21_confirmado') is not True:
            raise ArcaError('Confirmá que los conceptos están gravados íntegramente al 21% de IVA.')
        env=_environment()
        cuit=os.environ.get('ARCA_CUIT','').strip()
        pv=int(os.environ.get('ARCA_PUNTO_VENTA','0'))
        if len(cuit)!=11 or not cuit.isdigit() or not 1<=pv<=99999:
            raise ArcaError('Configurar CUIT y punto de venta autorizados en Render.')
        bid=int(data.get('borrador_id') or 0)
        if bid<=0: raise ArcaError('Falta el borrador fiscal.')
        # IMPORTANTE: se conserva el bloqueo de una fila Postgres mientras dura
        # la emisión para serializar dos operadores del mismo POS. No hay auto-retry.
        with transaction.atomic():
            lock,_ = ConfiguracionFiscal.objects.get_or_create(pk=1)
            ConfiguracionFiscal.objects.select_for_update().get(pk=lock.pk)
            borrador=BorradorFiscal.objects.select_for_update().get(pk=bid)
            factura=FacturaFiscal.objects.filter(borrador=borrador).first()
            if factura:
                if factura.entorno!=env or factura.cuit_emisor!=cuit or factura.punto_venta!=pv:
                    raise ArcaError('El borrador fue utilizado con otra configuración fiscal.')
                if factura.estado=='autorizada':
                    return JsonResponse(_serialize(factura))
                # Estado incierto o rechazado -> no reintentar sin investigación.
                return JsonResponse({'status':'error','estado':factura.estado,
                    'mensaje':'Esta operación ya fue intentada. Verificá en ARCA antes de volver a emitir.'},status=409)
            total=_validar_borrador(borrador)
            fch=timezone.localdate().strftime('%Y%m%d')
            factura=FacturaFiscal.objects.create(borrador=borrador, estado='incierto',
                entorno=env,cuit_emisor=cuit,punto_venta=pv,total=total,fecha_comprobante=fch,
                observaciones='Emisión iniciada. Si falla, verificar el número en ARCA.')
            try:
                n=ultimo_autorizado(pv,6)+1
                factura.numero=n
                factura.save(update_fields=['numero'])
                resultado=emitir_factura_b(pv,n,total,fch)
                factura.cae=resultado['cae']
                factura.vencimiento_cae=resultado['vencimiento']
                factura.neto_21=Decimal(resultado['neto'])
                factura.iva_21=Decimal(resultado['iva'])
                factura.url_qr=url_qr(cuit,pv,n,fch,total,factura.cae)
                factura.estado='autorizada'
                factura.observaciones=''
                factura.save()
            except ArcaIncierto as exc:
                factura.observaciones=str(exc)
                factura.save(update_fields=['observaciones'])
            except ArcaError as exc:
                # Rechazo explícito -> no supone que exista CAE.
                # Si hay número reservado, consulta antes de cualquier decisión nueva.
                factura.observaciones=str(exc)
                factura.estado='incierto' if factura.numero else 'rechazada'
                factura.save(update_fields=['observaciones','estado'])
            except Exception:
                # Ante cualquier error inesperado, jamás marcar como no emitida
                # una petición que pudo haberse autorizado remotamente.
                factura.estado='incierto'
                factura.observaciones='Error inesperado. Consultar ARCA antes de continuar.'
                factura.save(update_fields=['estado','observaciones'])
        if factura.estado == 'autorizada': return JsonResponse(_serialize(factura))
        return JsonResponse({'status':'error','estado':factura.estado,
            'factura_id':factura.pk,'mensaje':factura.observaciones[:350]},status=409)
    except (BorradorFiscal.DoesNotExist,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        return JsonResponse({'status':'error','mensaje':'Borrador o solicitud fiscal inválida.'},status=400)
    except ArcaError as exc:
        return JsonResponse({'status':'error','mensaje':str(exc)},status=409)


@require_POST
def consultar_incierta(request, factura_id):
    """Solo recupera una autorización existente; nunca crea nueva factura."""
    if not _login(request): return JsonResponse({'status':'error','mensaje':'No autorizado.'},status=403)
    try:
        with transaction.atomic():
            lock,_ = ConfiguracionFiscal.objects.get_or_create(pk=1)
            ConfiguracionFiscal.objects.select_for_update().get(pk=lock.pk)
            fac=FacturaFiscal.objects.select_for_update().get(pk=factura_id)
            if fac.estado=='autorizada': return JsonResponse(_serialize(fac))
            if not fac.numero:
                return JsonResponse({'status':'aviso','mensaje':'No se asignó número. Revisar antes de reintentar.'},status=409)
            if _environment()!=fac.entorno or os.environ.get('ARCA_CUIT','')!=fac.cuit_emisor:
                raise ArcaError('No coincide el entorno o CUIT de la factura original.')
            resultado=consultar(fac.punto_venta,6,fac.numero)
            if not resultado:
                return JsonResponse({'status':'aviso', 'mensaje':'ARCA no encontró el comprobante. No reenviar automáticamente.'},status=409)
            # Nunca asociar un CAE si el total o la fecha no corresponden.
            if Decimal(resultado['total']).quantize(Decimal('.01')) != fac.total or resultado['fecha'] != fac.fecha_comprobante:
                raise ArcaError('Número ocupado por un comprobante diferente. Revisión manual obligatoria.')
            fac.cae=resultado['cae'];fac.vencimiento_cae=resultado['vencimiento']
            fac.url_qr=url_qr(fac.cuit_emisor,fac.punto_venta,fac.numero,fac.fecha_comprobante,fac.total,fac.cae)
            fac.estado='autorizada';fac.observaciones=''
            fac.save()
            return JsonResponse(_serialize(fac))
    except FacturaFiscal.DoesNotExist:
        return JsonResponse({'status':'error','mensaje':'Factura no encontrada.'},status=404)
    except ArcaError as exc:
        return JsonResponse({'status':'error','mensaje':str(exc)},status=409)


def _authorized_printer(request):
    expected=os.environ.get('TICKETERA_PRINT_TOKEN','').strip()
    received=request.headers.get('X-Ticketera-Token','')
    if not expected or not received: return False
    import secrets
    return secrets.compare_digest(expected,received)


@require_GET
def tickets_fiscales_pendientes(request):
    if not _authorized_printer(request): return JsonResponse({'status':'error'},status=403)
    qs=FacturaFiscal.objects.select_related('borrador').filter(estado='autorizada',impresion_confirmada=False).order_by('creado')[:30]
    return JsonResponse({'status':'ok','tickets':[
        {'id':f.id,'entorno':f.entorno,'cuit':f.cuit_emisor,
         'razon_social':os.environ.get('ARCA_RAZON_SOCIAL', settings.RESTAURANT_NAME),
         'domicilio':os.environ.get('ARCA_DOMICILIO',''),
         'condicion_iva_emisor':os.environ.get('ARCA_CONDICION_IVA',''),
         'ingresos_brutos':os.environ.get('ARCA_INGRESOS_BRUTOS',''),
         'inicio_actividades':os.environ.get('ARCA_INICIO_ACTIVIDADES',''),
         'mesa':f.borrador.mesa,'mozo':f.borrador.mozo,
         'items':f.borrador.items,'total':str(f.total),
         'numero':f'{f.punto_venta:05d}-{f.numero:08d}',
         'fecha':f.fecha_comprobante,'cae':f.cae,
         'vencimiento_cae':f.vencimiento_cae,'url_qr':f.url_qr}
        for f in qs]})


@csrf_exempt
@require_POST
def confirmar_impresion(request, factura_id):
    if not _authorized_printer(request): return JsonResponse({'status':'error'},status=403)
    count=FacturaFiscal.objects.filter(pk=factura_id,estado='autorizada').update(
        impresion_confirmada=True, fecha_impresion=timezone.now())
    return JsonResponse({'status':'ok' if count else 'error'},status=200 if count else 404)
