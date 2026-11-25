"""Paneles separados: propietario Desktop / propietario Render."""
from django.conf import settings
from decimal import Decimal, InvalidOperation
from django.db.models import Count
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from desktop6c.models import DesktopLink
from .models import Desktop6eOutbox, Desktop6eInbox, Desktop6eSettings
from .sender import ReceptorNoListo, comprobar_receptor, enviar_pendientes
from .reconcile import reconcile


def _owner(request):
    return bool(request.user.is_authenticated and request.user.is_active and request.user.is_superuser)


def _local():return bool(getattr(settings,'STERAK_DESKTOP_MODE',False))


@never_cache
def estado(request):
    if not _local():return HttpResponseForbidden('Solo Desktop.')
    if not _owner(request):return HttpResponseForbidden('Ingresá como propietario local desde Vincular.')
    ajustes,_=Desktop6eSettings.objects.get_or_create(pk=1)
    return render(request,'desktop6e/local.html',{
        'ajustes':ajustes,'vinculo':DesktopLink.objects.first(),
        'pendientes':Desktop6eOutbox.objects.filter(status='pendiente').count(),
        'confirmados':Desktop6eOutbox.objects.filter(status='confirmado').count(),
        'eventos':Desktop6eOutbox.objects.all().order_by('-created_at')[:25],
        'mensaje':request.session.pop('6e_mensaje',''),
    })


@require_POST
def accion(request):
    if not _local() or not _owner(request):return HttpResponseForbidden('Solo propietario local.')
    act=request.POST.get('accion','')
    mensaje=''
    try:
        if act=='reconstruir':
            n=reconcile()
            mensaje=f'Revisión de seguridad completada: {n} registros locales examinados, sin duplicar eventos.'
        elif act=='probar':
            comprobar_receptor()
            mensaje='Receptor Render 6E disponible; identidad web verificada.'
        elif act=='enviar':
            info=enviar_pendientes(limite=10,habilitacion_requerida=False)
            mensaje=f"Enviados {info['enviados']} eventos. Pendientes: {info['pendientes']}."
        elif act=='habilitar':
            if request.POST.get('confirmacion','')!='HABILITAR 6E':
                raise ReceptorNoListo('Escribí HABILITAR 6E para activar el envío automático.')
            comprobar_receptor()
            Desktop6eSettings.objects.update_or_create(pk=1,defaults={'enviar_automaticamente':True})
            mensaje='Envío automático habilitado (cada 2 minutos).'
        elif act=='detener':
            Desktop6eSettings.objects.update_or_create(pk=1,defaults={'enviar_automaticamente':False})
            mensaje='Envío automático desactivado. Nada se perdió.'
        else:mensaje='Acción desconocida.'
    except ReceptorNoListo as exc:
        mensaje='ATENCIÓN: '+str(exc)
    except Exception as exc:
        mensaje='Error al procesar acción ('+exc.__class__.__name__+'). La cola permanece en SQLite.'
    request.session['6e_mensaje']=mensaje
    return redirect('desktop6c:sync6e_status')


@never_cache
def recibidos(request):
    if _local():return HttpResponseForbidden('Solo Render.')
    if not _owner(request):return HttpResponseForbidden('Solo propietario web.')
    # Registro espejo: ventas locales NO entran en Pedido, para evitar doble caja/CAE.
    datos=Desktop6eInbox.objects.all()
    resumen={x['tipo']:x['cantidad'] for x in datos.values('tipo').annotate(cantidad=Count('event_id'))}
    medios={x:Decimal('0') for x in ('efectivo','debito','mercadopago','cuenta_corriente')}
    for tipo, payload in datos.filter(tipo__in=['venta.salon','cobro.para_llevar']).values_list('tipo','payload').iterator(chunk_size=500):
        medio=payload.get('medio') if isinstance(payload,dict) else None
        if medio in medios:
            try:medios[medio]+=Decimal(str(payload['total']))
            except (KeyError,InvalidOperation,ValueError):pass
    return render(request,'desktop6e/web.html',{
        'eventos':datos[:150],'resumen':resumen,'total':datos.count(),
        'medios':medios,
    })
