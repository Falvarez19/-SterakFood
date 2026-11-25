"""Panel interno 6D. No lee credenciales fiscales y no envía operaciones web."""
import ipaddress
from decimal import Decimal
from django.conf import settings
from django.db.models import Q, Sum
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from pedidos.models import (Pedido, CuentaCorriente, MovimientoCuentaCorriente,
                            ConfiguracionImpresorasPOS, RespaldoMesasLocal)
from .models import ImpresionLocal6D, AjustesDesktop6D


def _permitido(request):
    return bool(getattr(settings, 'STERAK_DESKTOP_MODE', False) and
                request.session.get('dashboard_auth'))


def _owner(request):
    return _permitido(request) and request.user.is_authenticated and request.user.is_superuser


def _monto(queryset):
    return queryset.aggregate(s=Sum('total'))['s'] or Decimal('0.00')


@never_cache
def panel(request):
    if not _permitido(request):
        return HttpResponseForbidden('Ingresá primero con el PIN local del POS.')
    vendidos = (Pedido.objects.filter(archivado_ventas=False).exclude(estado='cancelado')
                .exclude(tipo_pago__in=['pendiente_para_llevar','ticket_salon_temporal'])
                .filter(Q(estado__in=['listo','entregado']) |
                        Q(tipo_entrega='para_llevar',tipo_pago__in=['efectivo','debito','mercadopago'])))
    desglose = {medio: _monto(vendidos.filter(tipo_pago=medio)) for medio in ('efectivo','debito','mercadopago')}
    # La cuenta corriente registra deuda, no ingreso a caja.
    fiado = _monto(vendidos.filter(tipo_pago='cuenta_corriente'))
    deuda = MovimientoCuentaCorriente.objects.aggregate(s=Sum('monto'))['s'] or Decimal('0')
    ajuste = AjustesDesktop6D.objects.filter(pk=1).first()
    respaldo = RespaldoMesasLocal.objects.filter(pk=1).first()
    return render(request, 'desktop6d/panel.html', {
        'cobros': desglose, 'fiado': fiado, 'total_cobrado':sum(desglose.values(),Decimal('0')),
        'saldo_global_cuentas': deuda,
        'cantidad_cuentas': CuentaCorriente.objects.filter(activa=True).count(),
        'pedidos_para_llevar': Pedido.objects.filter(tipo_entrega='para_llevar', tipo_pago='pendiente_para_llevar').count(),
        'respaldo_mesas': bool(respaldo and respaldo.version > 0),
        'respaldo_version': respaldo.version if respaldo else 0,
        'impresiones_pendientes': ImpresionLocal6D.objects.filter(estado='pendiente').count(),
        'impresiones_inciertas': ImpresionLocal6D.objects.filter(estado='incierto')[:30],
        'impresion_activa': bool(ajuste and ajuste.impresion_activa),
        'impresiones_ultimas': ImpresionLocal6D.objects.all()[:20],
    })


def _ip_local(valor):
    if not valor:
        raise ValueError('Configurá la IP privada de la impresora.')
    ip = ipaddress.ip_address(valor)
    if ip.version != 4 or not (ip.is_private or ip.is_link_local) or ip.is_loopback:
        raise ValueError('La impresora debe usar una IPv4 privada de la red local.')
    return str(ip)


@never_cache
def configurar_impresoras(request):
    if not _owner(request):
        return HttpResponseForbidden('Configuración exclusiva del propietario local.')
    cfg, _ = ConfiguracionImpresorasPOS.objects.get_or_create(pk=1)
    ajuste, _ = AjustesDesktop6D.objects.get_or_create(pk=1)
    error = ''
    mensaje = ''
    if request.method == 'POST':
        caja = (request.POST.get('caja') or '').strip()
        cocina = (request.POST.get('cocina') or '').strip()
        barra = (request.POST.get('barra') or '').strip()
        habilitar = request.POST.get('habilitar') == 'on'
        try:
            if not 1 <= len(caja) <= 120 or any(ord(c) < 32 for c in caja):
                raise ValueError('Escribí el nombre de la impresora Windows de caja.')
            # Las IP son obligatorias solo al activar la impresión.
            if habilitar:
                cocina = _ip_local(cocina)
                barra = _ip_local(barra)
            else:
                if cocina: cocina = _ip_local(cocina)
                if barra: barra = _ip_local(barra)
            cfg.caja_windows = caja
            if cocina: cfg.ip_cocina = cocina
            if barra: cfg.ip_barra = barra
            cfg.save(update_fields=['caja_windows','ip_cocina','ip_barra','actualizado'])
            ajuste.impresion_activa = habilitar
            ajuste.save(update_fields=['impresion_activa','actualizado'])
            mensaje = 'Impresoras configuradas. ' + ('El agente local podrá procesar la cola.' if habilitar else 'Impresión automática detenida.')
        except ValueError as exc:
            error = str(exc)
    return render(request,'desktop6d/impresoras.html',{'cfg':cfg,'ajuste':ajuste,'error':error,'mensaje':mensaje})


@require_POST
def resolver_incierta(request, registro_id):
    if not _owner(request):
        return HttpResponseForbidden('Acceso exclusivo del propietario.')
    reg = get_object_or_404(ImpresionLocal6D,pk=registro_id,estado='incierto')
    decision = request.POST.get('decision')
    if decision == 'marcar_enviado':
        reg.estado='enviado'
        reg.ultimo_error='Marcado como enviado tras revisión manual.'
        reg.save(update_fields=['estado','ultimo_error','actualizado'])
        from .printing import _finalizar_referencia
        _finalizar_referencia(reg)
    elif decision == 'reintentar':
        reg.estado='pendiente'
        reg.ultimo_error='Reimpresión autorizada manualmente por propietario.'
        reg.save(update_fields=['estado','ultimo_error','actualizado'])
    # Ninguna de las acciones borra ventas ni factura.
    return redirect('desktop6c:desktop6d:panel')
