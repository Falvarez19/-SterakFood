"""SterakFood 6F.9 R2: un formulario visual para Web y Desktop.

Web guarda preferencias web; solo Desktop controla las impresoras fisicas.
No sincroniza configuraciones entre SQLite y Render.
"""
from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseForbidden, HttpResponseNotAllowed
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .impresoras_views import validar_rutas_6f3
from .models import ConfiguracionImpresorasPOS


def _local():
    return bool(getattr(settings, 'STERAK_DESKTOP_MODE', False))


def _permiso(request):
    if not request.session.get('dashboard_auth'):
        return False
    if _local():
        return bool(request.user.is_authenticated and request.user.is_active and request.user.is_superuser)
    return True  # Misma autorizacion existente del panel web de impresoras.


def _trabajos_locales():
    from desktop6d.models import ImpresionLocal6D
    from pedidos.models import Pedido, ImpresionComprobanteCuenta
    pendientes = ImpresionLocal6D.objects.filter(estado__in=('pendiente','enviando')).count()
    inciertos = ImpresionLocal6D.objects.filter(estado='incierto').count()
    # Tambien hay tickets que el agente todavia no descubrio en su tabla.
    por_descubrir = (
        Pedido.objects.filter(impreso_caja=False, tipo_pago='ticket_salon_temporal').count()
        + Pedido.objects.filter(impreso_caja=False, tipo_entrega='para_llevar').exclude(estado='cancelado').count()
        + ImpresionComprobanteCuenta.objects.filter(impreso=False).count()
    )
    return pendientes, inciertos, por_descubrir


@never_cache
def impresoras_unificadas(request):
    if not _permiso(request):
        return HttpResponseForbidden('Acceso limitado al responsable del POS.')
    if request.method not in ('GET', 'POST'):
        return HttpResponseNotAllowed(['GET', 'POST'])

    es_local = _local()
    cfg, _ = ConfiguracionImpresorasPOS.objects.get_or_create(pk=1)
    ajuste = None
    habilitada = False
    pendientes = inciertos = por_descubrir = 0
    detectadas = []
    advertencia = ''
    error = ''
    mensaje = ''

    if es_local:
        from desktop6d.models import AjustesDesktop6D
        ajuste, _ = AjustesDesktop6D.objects.get_or_create(pk=1)
        habilitada = ajuste.impresion_activa
        pendientes, inciertos, por_descubrir = _trabajos_locales()
        from desktop6d.printer_discovery import impresoras_instaladas
        detectadas, advertencia = impresoras_instaladas()

    if request.method == 'POST':
        try:
            datos = validar_rutas_6f3(request.POST)
            activar = es_local and request.POST.get('habilitar') == 'on'
            if es_local and activar and not habilitada and (pendientes or inciertos or por_descubrir):
                if request.POST.get('revisado') != 'si':
                    raise ValueError('Hay tickets previos por revisar. Confirmalos antes de activar el agente.')
            with transaction.atomic():
                for campo, valor in datos.items():
                    setattr(cfg, campo, valor)
                cfg.save(update_fields=[*datos.keys(), 'actualizado'])
                if es_local:
                    ajuste.impresion_activa = activar
                    ajuste.save(update_fields=['impresion_activa','actualizado'])
                    habilitada = activar
            mensaje = ('Configuracion local guardada.' if es_local else 'Preferencias web guardadas en Render.')
        except (ValueError, TypeError, OverflowError) as exc:
            error = str(exc)

    return render(request, 'pedidos/impresoras_unificadas.html', {
        'cfg': cfg, 'es_local': es_local, 'habilitada': habilitada,
        'error': error, 'mensaje': mensaje,
        'detectadas': detectadas, 'advertencia': advertencia,
        'pendientes': pendientes, 'inciertos': inciertos, 'por_descubrir': por_descubrir,
    })


@require_POST
def prueba_local(request, sector):
    """Una prueba no fiscal. No altera cola, mesas, caja ni Render."""
    if not _local():
        return HttpResponseForbidden('Render no puede imprimir en las impresoras del local.')
    if not _permiso(request):
        return HttpResponseForbidden('Acceso exclusivo del propietario Desktop.')
    if sector not in ('caja','cocina','barra'):
        return HttpResponseForbidden('Destino no valido.')

    # Evita doble click sobre Probar y reimpresion involuntaria en segundos.
    ahora = timezone.now().timestamp()
    anterior = float(request.session.get('sf69_test_ts', 0))
    if ahora - anterior < 12:
        messages.error(request, 'Esperá unos segundos antes de otra prueba.')
        return redirect('pedidos:impresoras_unificadas')
    request.session['sf69_test_ts'] = ahora

    from desktop6d.printing import _raw, _send_windows, _send_network
    from desktop6d.views import _ip_local
    cfg = ConfiguracionImpresorasPOS.objects.filter(pk=1).first()
    if not cfg:
        messages.error(request, 'Guardá la configuracion primero.')
        return redirect('pedidos:impresoras_unificadas')
    datos = _raw([
        'STERAKFOOD', 'PRUEBA DE IMPRESION',
        'DESTINO: ' + sector.upper(), 'NO FISCAL',
        'SIN VENTA NI COBRO', 'SIN COMANDA REAL',
    ])
    try:
        modo = getattr(cfg, sector + '_modo', 'off')
        if modo == 'windows':
            nombre = getattr(cfg, sector + '_windows', '')
            if not nombre:
                raise ValueError('No hay impresora Windows configurada.')
            _send_windows(nombre, datos)
        elif modo == 'tcp':
            campo = 'caja_ip' if sector == 'caja' else 'ip_' + sector
            _send_network(_ip_local(getattr(cfg, campo, '') or ''), datos)
        else:
            raise ValueError('Este destino esta desactivado.')
    except Exception as exc:
        messages.error(request, 'Resultado no confirmado: ' + str(exc)[:180] + '. Revisá la impresora antes de reintentar.')
    else:
        messages.success(request, 'Prueba enviada a ' + sector + '. Verificá fisicamente que salio.')
    return redirect('pedidos:impresoras_unificadas')
