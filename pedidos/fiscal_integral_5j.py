"""SterakFood 5J. Facturación A/B/C para ventas de bienes nacionales en ARS.

GUARDAS: homologación por defecto, sólo manual, origen servidor, anti-duplicados,
primero registrar intención, luego pedir CAE, ante dudas consultar; nunca retry automático.
Para responsables inscriptos se limita a ventas 100 % gravadas al IVA 21 %:
NO soporta otros IVA, exentos, servicios, notas de crédito, percepciones ni FCE MiPyME.
"""
from __future__ import annotations

import base64
import json
import os
import re
import uuid
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import datetime
from xml.etree import ElementTree as ET

from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from .models import BorradorFiscal, ConfiguracionFiscal, FacturaFiscal, Pedido, DetallePedido
from .arca_wsfe import (ArcaError, ArcaIncierto, WSFE_NS, URLS,
                        _soap_post, _first, _value, _add, _get_token, ultimo_autorizado,
                        consultar)
from marca.models import ArcaCredencial
from marca.arca_vault_5a import runtime_emision, ConfiguracionSeguraError

TIPOS = {1:'A',6:'B',11:'C'}


def _entero(value, limite=999999999):
    x = int(value)
    if x < 0 or x > limite: raise ValueError('Número fuera de rango.')
    return x


def _dinero(value):
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number <= 0 or number >= Decimal('1000000000'):
            raise ValueError()
        if number != number.quantize(Decimal('.01')): raise ValueError()
        return number
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ArcaError('El importe tiene que ser positivo, válido y con dos decimales.') from exc


def _cuit_valido(numero):
    if not re.fullmatch(r'\d{11}', str(numero)): return False
    pesos=(5,4,3,2,7,6,5,4,3,2)
    r=11-(sum(int(a)*b for a,b in zip(numero[:10],pesos))%11)
    return int(numero[-1]) == (0 if r==11 else 9 if r==10 else r)


def _receptor(datos, emisor, total):
    condicion = str(datos.get('condicion_receptor') or 'consumidor_final').lower().strip()
    codigos={'consumidor_final':5,'responsable_inscripto':1,'monotributo':6}
    if condicion not in codigos: raise ArcaError('Condición del receptor no habilitada en esta versión.')
    documento = re.sub(r'[-\s]', '', str(datos.get('numero_documento') or ''))
    nombre = str(datos.get('nombre_receptor') or '').strip()[:150]
    if condicion == 'consumidor_final':
        if documento:
            if len(documento) in (7,8) and documento.isdigit(): tipo_doc=96
            elif _cuit_valido(documento): tipo_doc=80
            else: raise ArcaError('El documento del consumidor final no es válido.')
        else:
            # Límite deliberadamente conservador hasta validar reglas de identificación.
            if total > Decimal('100000.00'):
                raise ArcaError('Para este importe ingresá DNI o CUIT del receptor. La validación legal final está pendiente.')
            tipo_doc=99;documento='0'
    else:
        if not _cuit_valido(documento):
            raise ArcaError('Para empresas o monotributistas se requiere un CUIT válido del receptor.')
        tipo_doc=80
        if not nombre: raise ArcaError('Ingresá el nombre o razón social del receptor.')
    if emisor == 'ri':
        tipo = 1 if condicion == 'responsable_inscripto' else 6
    elif emisor == 'monotributo':
        tipo = 11
    else:
        raise ArcaError('La condición fiscal del emisor todavía no está soportada.')
    return {'tipo':tipo,'iva_receptor':codigos[condicion], 'doc_tipo':tipo_doc,
            'doc_nro':documento,'nombre':nombre or 'Consumidor Final'}


def calcular(importea, tipo):
    total=_dinero(importea)
    if tipo==11: return {'total':total,'neto':total,'iva':Decimal('0.00')}
    if tipo not in (1,6): raise ArcaError('Tipo de factura desconocido.')
    # Únicamente mercancías 21 %: nunca inferir alícuota del catálogo.
    neto=(total/Decimal('1.21')).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
    return {'total':total,'neto':neto,'iva':total-neto}


def armar_solicitud(token,sign,cuit,pv,tipo,numero,fecha,importe,receptor):
    """XML SOAP namespace-safe; no network. Tests cover IVA and recipient."""
    montos=calcular(importe,tipo)
    op=ET.Element(f'{{{WSFE_NS}}}FECAESolicitar')
    auth=ET.SubElement(op,f'{{{WSFE_NS}}}Auth')
    for k,v in [('Token',token),('Sign',sign),('Cuit',cuit)]: _add(auth,f'{{{WSFE_NS}}}{k}',v)
    req=ET.SubElement(op,f'{{{WSFE_NS}}}FeCAEReq')
    cab=ET.SubElement(req,f'{{{WSFE_NS}}}FeCabReq')
    for k,v in [('CantReg',1),('PtoVta',pv),('CbteTipo',tipo)]: _add(cab,f'{{{WSFE_NS}}}{k}',v)
    detalle=ET.SubElement(ET.SubElement(req,f'{{{WSFE_NS}}}FeDetReq'),f'{{{WSFE_NS}}}FECAEDetRequest')
    valores=[('Concepto',1),('DocTipo',receptor['doc_tipo']),('DocNro',receptor['doc_nro']),
       ('CbteDesde',numero),('CbteHasta',numero),('CbteFch',fecha),
       ('ImpTotal',f"{montos['total']:.2f}"),('ImpTotConc','0.00'),
       ('ImpNeto',f"{montos['neto']:.2f}"),('ImpOpEx','0.00'),('ImpTrib','0.00'),
       ('ImpIVA',f"{montos['iva']:.2f}"),('MonId','PES'),('MonCotiz',1)]
    for k,v in valores: _add(detalle,f'{{{WSFE_NS}}}{k}',v)
    if tipo in (1,6):
        impuestos=ET.SubElement(detalle,f'{{{WSFE_NS}}}Iva')
        alic=ET.SubElement(impuestos,f'{{{WSFE_NS}}}AlicIva')
        for k,v in [('Id',5),('BaseImp',f"{montos['neto']:.2f}"),('Importe',f"{montos['iva']:.2f}")]:
            _add(alic,f'{{{WSFE_NS}}}{k}',v)
    _add(detalle,f'{{{WSFE_NS}}}CondicionIVAReceptorId',receptor['iva_receptor'])
    return op


def interpretar(root,numero):
    detalle=_first(root,'FECAEDetResponse')
    if detalle is None: raise ArcaIncierto('Respuesta sin detalle de comprobante. Consultar ARCA.')
    estado=_value(detalle,'Resultado')
    cae=_value(detalle,'CAE'); vence=_value(detalle,'CAEFchVto')
    if estado=='R': raise ArcaError('ARCA rechazó el comprobante. Verificar observaciones y numeración.')
    if (estado!='A' or not re.fullmatch(r'\d{10,20}',cae)
        or not re.fullmatch(r'\d{8}',vence)):
        raise ArcaIncierto('ARCA no confirmó un CAE válido. Revisar antes de reintentar.')
    for field in ('CbteDesde','CbteHasta'):
        value=_value(detalle,field)
        if value and value!=str(numero): raise ArcaIncierto('Numeración distinta a la reservada.')
    return cae, vence


def url_qr(factura):
    data={'ver':1,'fecha':f'{factura.fecha_comprobante[:4]}-{factura.fecha_comprobante[4:6]}-{factura.fecha_comprobante[6:8]}',
          'cuit':int(factura.cuit_emisor),'ptoVta':factura.punto_venta,
          'tipoCmp':factura.tipo_comprobante,'nroCmp':factura.numero,
          'importe':float(factura.total),'moneda':'PES','ctz':1,
          'tipoDocRec':factura.receptor_tipo_documento,
          'nroDocRec':int(factura.receptor_numero_documento or '0'),
          'tipoCodAut':'E','codAut':int(factura.cae)}
    return 'https://www.arca.gob.ar/fe/qr/?p='+base64.b64encode(json.dumps(data,separators=(',',':')).encode()).decode()


def _autorizado(request):
    return bool(request.session.get('dashboard_auth'))


def _runtime_validado():
    runtime=runtime_emision()  # Bóveda y activación obligatorias, NO variables ARCA viejas.
    if runtime is None:
        raise ArcaError('Primero completá las migraciones y la configuración segura de ARCA.')
    fiscal=ConfiguracionFiscal.objects.filter(pk=1).first()
    if fiscal is None:
        raise ArcaError('Primero completá los datos fiscales desde Mi negocio.')
    if fiscal.condicion_iva not in ('ri','monotributo'):
        raise ArcaError('El régimen fiscal configurado todavía no puede facturar con este motor.')
    if (runtime.cuit != fiscal.cuit or runtime.punto_venta != fiscal.punto_venta_referencia):
        raise ArcaError('Cambió la configuración fiscal. Verificá y activá de nuevo desde Mi negocio.')
    fila=ArcaCredencial.objects.filter(activa=True,entorno=runtime.entorno,cuit=runtime.cuit).first()
    if not fila or not fila.verificada or fila.punto_venta!=runtime.punto_venta:
        raise ArcaError('Falta autorización del certificado en Mi negocio.')
    if runtime.entorno != 'homologacion':
        # Activación de producción requiere certificación específica de esta versión.
        # NO dar por habilitada producción por una variable heredada.
        raise ArcaError('Versión 5J: producción bloqueada hasta aprobar homologación y auditoría fiscal.')
    return runtime,fiscal


def _validar_borrador(b):
    if b.mesa.startswith('PL'):
        pedido_id=int(b.mesa[2:])
        pedido=(Pedido.objects.filter(pk=pedido_id,tipo_entrega='para_llevar')
                .exclude(tipo_pago='pendiente_para_llevar').exclude(estado='cancelado').first())
        if pedido is None: raise ArcaError('El pedido Para llevar no está cobrado o fue cancelado.')
        lineas=list(DetallePedido.objects.filter(pedido=pedido))
        monto=sum((x.precio_unitario*x.cantidad for x in lineas),Decimal('0.00'))
        if monto!=b.total_estimado or monto!=pedido.total:
            raise ArcaError('El total del pedido cambió. Necesita revisión.')
        return monto
    from .fiscal_views import _validar_borrador
    return _validar_borrador(b)


def _nuevo_borrador_para_llevar(pedido_id):
    with transaction.atomic():
        p=(Pedido.objects.select_for_update().filter(pk=pedido_id,tipo_entrega='para_llevar',
                          para_llevar__isnull=False).first())
        if p is None or p.estado=='cancelado' or p.tipo_pago not in ('efectivo','debito','mercadopago'):
            raise ArcaError('Solo se puede facturar un pedido Para llevar cobrado y válido.')
        lineas=list(DetallePedido.objects.filter(pedido=p).select_related('producto'))
        if not lineas: raise ArcaError('El pedido está vacío.')
        total=sum((i.precio_unitario*i.cantidad for i in lineas),Decimal('0.00'))
        if total!=p.total: raise ArcaError('El pedido cambió de importe; revisalo antes de facturar.')
        items=[{'producto_id':str(i.producto_id or ''),'nombre':i.producto.nombre if i.producto else 'Producto',
                'precio':str(i.precio_unitario),'cantidad':i.cantidad,'subtotal':str(i.precio_unitario*i.cantidad),
                'detalle_id':str(i.id),'pedido_id':str(p.pk)} for i in lineas]
        opid=uuid.uuid5(uuid.NAMESPACE_URL,f'sterakfood-fiscal:para-llevar:{p.pk}')
        b, created=BorradorFiscal.objects.get_or_create(operacion_id=opid,
            defaults={'mesa':'PL'+str(p.pk),'mozo':'Para llevar',
                      'items':items,'total_estimado':total})
        if b.total_estimado!=total or b.items!=items:
            raise ArcaError('Ya existe un borrador diferente para este pedido. Revisar manualmente.')
        return b


def _respuesta(f):
    return {'status':'ok' if f.estado=='autorizada' else 'aviso',
       'id':f.pk,'estado':f.estado,'tipo':TIPOS.get(f.tipo_comprobante,'?'),
       'numero':f'{f.punto_venta:05d}-{(f.numero or 0):08d}',
       'cae':f.cae,'vencimiento':f.vencimiento_cae,'total':str(f.total),
       'mensaje':f.observaciones or ('CAE autorizado en HOMOLOGACIÓN; sin valor fiscal.' if f.estado=='autorizada' else 'Verificar en ARCA antes de reintentar.')}


@never_cache
@require_POST
def emitir_manual_5j(request):
    if not _autorizado(request): return JsonResponse({'status':'error','mensaje':'Sesión POS requerida.'},status=403)
    try:
        if len(request.body)>40_000: raise ArcaError('Solicitud demasiado grande.')
        data=json.loads(request.body.decode('utf-8'))
        if not isinstance(data,dict) or data.get('confirmacion')!='FACTURAR_CON_ASTERISCO':
            raise ArcaError('Se requiere confirmación manual del operador.')
        bid=_entero(data.get('borrador_id'))
        if bid<=0: raise ArcaError('Elegí un borrador fiscal.')
        return _procesar(bid,data)
    except (ValueError,TypeError,UnicodeError,json.JSONDecodeError,ArcaError,ConfiguracionSeguraError) as e:
        return JsonResponse({'status':'error','mensaje':str(e)[:300]},status=409)


@never_cache
@require_POST
def facturar_para_llevar_5j(request,pedido_id):
    if not _autorizado(request): return JsonResponse({'status':'error','mensaje':'Sesión POS requerida.'},status=403)
    try:
        if len(request.body)>40_000: raise ArcaError('Solicitud demasiado grande.')
        data=json.loads(request.body.decode('utf-8'))
        if not isinstance(data,dict) or data.get('confirmacion')!='FACTURAR_CON_ASTERISCO':
            raise ArcaError('La Factura C/A/B requiere confirmación manual.')
        b=_nuevo_borrador_para_llevar(pedido_id)
        return _procesar(b.pk,data)
    except (ValueError,TypeError,UnicodeError,json.JSONDecodeError,ArcaError,ConfiguracionSeguraError) as e:
        return JsonResponse({'status':'error','mensaje':str(e)[:300]},status=409)


def _procesar(bid,data):
    runtime,fiscal=_runtime_validado()
    with transaction.atomic():
        # SERIALIZACIÓN en PostgreSQL: controla números incluso entre cajas.
        ConfiguracionFiscal.objects.select_for_update().get(pk=fiscal.pk)
        b=BorradorFiscal.objects.select_for_update().get(pk=bid)
        anterior=FacturaFiscal.objects.filter(borrador=b).first()
        if anterior:
            if anterior.cuit_emisor!=runtime.cuit or anterior.entorno!=runtime.entorno:
                raise ArcaError('Este borrador pertenece a otro emisor. Revisión manual.')
            if anterior.estado=='autorizada': return JsonResponse(_respuesta(anterior))
            return JsonResponse({'status':'aviso','estado':anterior.estado,'id':anterior.pk,
                'mensaje':'Operación ya intentada. Consultá antes de reintentar.'},status=409)
        total=_dinero(_validar_borrador(b))
        receptor=_receptor(data,fiscal.condicion_iva,total)
        if fiscal.condicion_iva=='ri' and data.get('iva_21_confirmado') is not True:
            raise ArcaError('Confirmá que toda esta venta está gravada al 21 % de IVA.')
        tipo=receptor['tipo']
        if FacturaFiscal.objects.filter(entorno=runtime.entorno,cuit_emisor=runtime.cuit,
            punto_venta=runtime.punto_venta,tipo_comprobante=tipo,
            estado__in=['incierto','pendiente']).exists():
            raise ArcaError('Hay un comprobante sin resolver de este tipo. Consultalo antes de continuar.')
        if tipo==11:
            from marca.models import ArcaEnsayoFacturaC
            if ArcaEnsayoFacturaC.objects.filter(entorno=runtime.entorno, cuit_emisor=runtime.cuit,
                punto_venta=runtime.punto_venta).exclude(estado='autorizada').exists():
                raise ArcaError('Ensayo C anterior sin resolver. Consultalo desde Mi negocio antes de emitir.')
        # ARCA de solo lectura: en una transacción protegida para reservar N.
        proximo=ultimo_autorizado(runtime.punto_venta,tipo)+1
        if proximo>99999999: raise ArcaError('Se agotó la numeración fiscal.')
        montos=calcular(total,tipo)
        p_id=int(b.mesa[2:]) if b.mesa.startswith('PL') else None
        f=FacturaFiscal.objects.create(
           borrador=b,estado='incierto',entorno=runtime.entorno,cuit_emisor=runtime.cuit,
           punto_venta=runtime.punto_venta,tipo_comprobante=tipo,numero=proximo,
           fecha_comprobante=timezone.localdate().strftime('%Y%m%d'),total=total,
           neto_21=montos['neto'] if tipo!=11 else Decimal('0'),iva_21=montos['iva'],
           receptor_tipo_documento=receptor['doc_tipo'],
           receptor_numero_documento=receptor['doc_nro'],
           receptor_condicion_iva=receptor['iva_receptor'],
           receptor_nombre=receptor['nombre'],
           origen='para_llevar' if p_id else 'salon',origen_pedido_id=p_id,
           observaciones='Solicitud reservada. Si se pierde la conexión, consultar ARCA antes de reintentar.')
    try:
        token,sign,cuit=_get_token(runtime.entorno)
        solicitud=armar_solicitud(token,sign,cuit,f.punto_venta,f.tipo_comprobante,
            f.numero,f.fecha_comprobante,f.total,receptor)
        response=_soap_post(URLS[runtime.entorno][1],WSFE_NS+'FECAESolicitar',solicitud)
        cae, vence=interpretar(response,f.numero)
        with transaction.atomic():
            obj=FacturaFiscal.objects.select_for_update().get(pk=f.pk)
            if obj.estado!='incierto': raise ArcaError('El estado de factura cambió durante la emisión.')
            obj.cae=cae;obj.vencimiento_cae=vence;obj.estado='autorizada'
            obj.url_qr=url_qr(obj);obj.observaciones='';obj.save()
            f=obj
    except (ArcaError, ArcaIncierto) as exc:
        # Incluso con rechazo explícito no reutilizar la numeración automáticamente.
        FacturaFiscal.objects.filter(pk=f.pk,estado='incierto').update(observaciones=str(exc)[:300])
    except Exception:
        FacturaFiscal.objects.filter(pk=f.pk,estado='incierto').update(
             observaciones='Respuesta incierta de ARCA. Consulta obligatoria; NO reenviar.')
    f=FacturaFiscal.objects.get(pk=f.pk)
    return JsonResponse(_respuesta(f),status=200 if f.estado=='autorizada' else 409)


@never_cache
@require_POST
def recuperar_5j(request,factura_id):
    if not _autorizado(request): return JsonResponse({'status':'error','mensaje':'Sesión POS requerida.'},status=403)
    try:
        runtime,_=_runtime_validado()
        with transaction.atomic():
            f=FacturaFiscal.objects.select_for_update().get(pk=factura_id)
            if f.entorno!=runtime.entorno or f.cuit_emisor!=runtime.cuit or f.punto_venta!=runtime.punto_venta:
                raise ArcaError('El comprobante fue creado con otra configuración fiscal.')
            if f.estado=='autorizada': return JsonResponse(_respuesta(f))
            if not f.numero: raise ArcaError('No hay número para consultar. Revisión manual.')
        encontrado=consultar(f.punto_venta,f.tipo_comprobante,f.numero)
        if not encontrado:
            return JsonResponse({'status':'aviso','mensaje':'ARCA no devolvió comprobante. No reenviar automáticamente.'},status=409)
        if encontrado['fecha']!=f.fecha_comprobante or _dinero(encontrado['total'])!=f.total:
            raise ArcaError('Los datos del comprobante encontrado no coinciden. Revisión manual obligatoria.')
        if (encontrado.get('doc_tipo') and int(encontrado['doc_tipo'])!=f.receptor_tipo_documento
            or encontrado.get('doc_nro') and encontrado['doc_nro']!=f.receptor_numero_documento):
            raise ArcaError('El receptor consultado no coincide. Revisión manual obligatoria.')
        with transaction.atomic():
            f=FacturaFiscal.objects.select_for_update().get(pk=f.pk)
            if f.estado!='autorizada':
                f.cae=encontrado['cae'];f.vencimiento_cae=encontrado['vencimiento'];
                f.estado='autorizada';f.observaciones='';f.url_qr=url_qr(f);f.save()
        return JsonResponse(_respuesta(f))
    except FacturaFiscal.DoesNotExist:
        return JsonResponse({'status':'error','mensaje':'No encontrado.'},status=404)
    except (ArcaError, ConfiguracionSeguraError, ValueError) as e:
        return JsonResponse({'status':'error','mensaje':str(e)[:250]},status=409)


@never_cache
@require_GET
def historial_5j(request):
    if not _autorizado(request):
        return JsonResponse({'status':'error','mensaje':'Iniciá sesión en el POS.'},status=403)
    filas=FacturaFiscal.objects.select_related('borrador').order_by('-creado')[:100]
    return render(request,'pedidos/fiscal_historial_5j.html',{'facturas':filas,'tipos':TIPOS})
