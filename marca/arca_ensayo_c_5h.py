"""Ensayo de emisión C con CAE, ÚNICAMENTE en homologación y fuera del POS.

Diseño conservador: registra la intención ANTES del POST a ARCA;
ante incertidumbre, NUNCA reenvía automáticamente y ofrece FECompConsultar.
Los certificados solo se toman de la bóveda de Mi negocio.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST

from .views import autorizado
from .models import ArcaEnsayoFacturaC, ArcaCredencial
from pedidos.models import ConfiguracionFiscal
from pedidos.arca_wsfe import URLS, _soap_post
from pedidos.arca_c_emision_5h import (
    WSFE_NS, FacturaCEnsayoError, FacturaCEnsayoRechazada,
    FacturaCEnsayoIncierta, total_ensayo, armar_solicitud_c,
    interpretar_emision_c, armar_consulta_c, leer_consulta_c, qr_url_c,
)
from .arca_vault_5a import cargar_runtime, _token_wsaa
from .arca_preflight_c_5g import verificar_preflight_c


def _origen_valido():
    fiscal = ConfiguracionFiscal.objects.filter(pk=1).first()
    if (fiscal is None or fiscal.condicion_iva != 'monotributo'
        or not fiscal.cuit or len(fiscal.cuit) != 11 or not fiscal.cuit.isdigit()
        or not fiscal.punto_venta_referencia):
        raise FacturaCEnsayoError('Seleccioná Monotributista y completá CUIT y punto de venta en Datos fiscales.')
    row = ArcaCredencial.objects.filter(entorno='homologacion').first()
    if (row is None or row.cuit != fiscal.cuit or row.punto_venta != fiscal.punto_venta_referencia):
        raise FacturaCEnsayoError('Cargá un P12 de homologación para ese CUIT y punto de venta.')
    runtime = cargar_runtime(row)
    if runtime.entorno != 'homologacion':
        raise FacturaCEnsayoError('Producción bloqueada para ensayos 5H.')
    return fiscal, runtime


def _marcar(ensayo, estado, mensaje, datos=None):
    with transaction.atomic():
        row = ArcaEnsayoFacturaC.objects.select_for_update().get(pk=ensayo.pk)
        if row.estado == 'autorizada':
            return row
        # Una consulta FECompConsultar puede recuperar también un rechazo aparente.
        row.estado = estado
        row.detalle_publico = mensaje[:240]
        if datos and estado == 'autorizada':
            row.cae = datos['cae']
            row.vence_cae = datos['vencimiento']
            row.url_qr = qr_url_c(row.cuit_emisor, row.punto_venta,
                                  row.numero, row.fecha_comprobante, row.total, row.cae)
        row.save(update_fields=['estado','detalle_publico','cae','vence_cae','url_qr','actualizado'])
        return row


@never_cache
@csrf_protect
@require_POST
def emitir_ensayo_c_5h(request):
    if not autorizado(request):
        return HttpResponseForbidden('Solo el propietario puede ejecutar ensayos fiscales.')
    if (request.POST.get('confirmacion') != 'ACEPTO_CAE_PRUEBA_5H'
        or request.POST.get('confirmo_otra_vez') != 'SI'):
        messages.error(request, 'Para solicitar un CAE de homologación, confirmá expresamente las dos casillas.')
        return redirect('marca:arca_propietario')

    try:
        total = total_ensayo(request.POST.get('importe', ''))
        # La fila fiscal única serializa las reservas de número entre operadores
        # en PostgreSQL. No mantenemos abierto el bloqueo durante el POST externo.
        with transaction.atomic():
            fiscal = ConfiguracionFiscal.objects.select_for_update().get(pk=1)
            if fiscal.condicion_iva != 'monotributo':
                raise FacturaCEnsayoError('El negocio no está configurado como monotributista.')
            _, runtime = _origen_valido()
            if ArcaEnsayoFacturaC.objects.filter(
                entorno='homologacion', cuit_emisor=runtime.cuit,
                punto_venta=runtime.punto_venta).exclude(estado='autorizada').exists():
                raise FacturaCEnsayoError(
                    'Hay un ensayo anterior sin resolver. Revisalo antes de solicitar otro CAE.')
            # Hace WSAA, FEParamGetPtosVenta y FECompUltimoAutorizado.
            preflight = verificar_preflight_c()
            numero = preflight['ultimo'] + 1
            if numero > 99999999:
                raise FacturaCEnsayoError('Se agotó la numeración para este punto de venta.')
            ensayo = ArcaEnsayoFacturaC.objects.create(
                entorno='homologacion', cuit_emisor=runtime.cuit,
                punto_venta=runtime.punto_venta, numero=numero,
                fecha_comprobante=timezone.localdate().strftime('%Y%m%d'),
                total=total, estado='incierto',
                detalle_publico='Solicitud reservada; verificar en ARCA antes de repetir.',
            )
        # La reserva ya está en DB antes de cualquier envío: un timeout no la borra.
        token, sign, cuit = _token_wsaa(runtime)
        solicitud = armar_solicitud_c(token, sign, cuit, ensayo.punto_venta,
                                    ensayo.numero, ensayo.total,
                                    ensayo.fecha_comprobante, entorno=runtime.entorno)
        respuesta = _soap_post(URLS['homologacion'][1], WSFE_NS + 'FECAESolicitar', solicitud)
        datos = interpretar_emision_c(respuesta, ensayo.numero)
        _marcar(ensayo, 'autorizada', 'CAE de HOMOLOGACIÓN obtenido; sin valor fiscal.', datos)
        messages.success(request, 'Ensayo C autorizado por ARCA HOMOLOGACIÓN. No es una factura real.')
    except FacturaCEnsayoRechazada:
        if 'ensayo' in locals():
            _marcar(ensayo, 'rechazada', 'Rechazada en homologación. Revisión manual obligatoria.')
        messages.warning(request, 'ARCA rechazó la prueba. No se reenvió la solicitud.')
    except FacturaCEnsayoError as exc:
        messages.warning(request, str(exc)[:240])
    except Exception:
        # Incluye pérdida de red y respuestas ambiguas: mantener incierto.
        messages.error(request, 'Resultado incierto o error de conexión. No reintentes: usá Consultar último ensayo.')
    return redirect('marca:arca_resultado_5h')


@never_cache
@csrf_protect
@require_POST
def recuperar_ensayo_c_5h(request):
    if not autorizado(request):
        return HttpResponseForbidden('Solo propietario.')
    try:
        fiscal, runtime = _origen_valido()
        row = (ArcaEnsayoFacturaC.objects.filter(
            entorno='homologacion', cuit_emisor=fiscal.cuit,
            punto_venta=fiscal.punto_venta_referencia).order_by('-creado').first())
        if not row:
            raise FacturaCEnsayoError('No hay ensayos de Factura C para consultar.')
        if row.estado == 'autorizada':
            messages.info(request, 'Este ensayo ya está registrado con CAE de homologación.')
            return redirect('marca:arca_resultado_5h')
        token, sign, cuit = _token_wsaa(runtime)
        consulta = armar_consulta_c(token, sign, cuit, row.punto_venta, row.numero, entorno='homologacion')
        respuesta = _soap_post(URLS['homologacion'][1], WSFE_NS + 'FECompConsultar', consulta)
        encontrado = leer_consulta_c(respuesta)
        if not encontrado:
            messages.warning(request, 'ARCA no devolvió un CAE para ese número. La operación sigue bloqueada hasta revisión manual.')
            return redirect('marca:arca_resultado_5h')
        if (not encontrado['cae'].isdigit() or
            encontrado['fecha'] != row.fecha_comprobante or
            (encontrado['numero'] and int(encontrado['numero']) != row.numero)):
            raise FacturaCEnsayoError('La consulta no coincide con el ensayo reservado. Revisión manual.')
        try:
            autorizado_total = Decimal(encontrado['total']).quantize(Decimal('.01'))
        except (InvalidOperation, TypeError):
            raise FacturaCEnsayoError('ARCA no devolvió un importe comparable.')
        if autorizado_total != row.total:
            raise FacturaCEnsayoError('El importe encontrado en ARCA no coincide. Revisión manual.')
        if not encontrado['vencimiento'] or len(encontrado['vencimiento']) != 8:
            raise FacturaCEnsayoError('Falta vencimiento de CAE: verificar manualmente.')
        _marcar(row, 'autorizada', 'CAE recuperado con FECompConsultar.',
                {'cae': encontrado['cae'], 'vencimiento': encontrado['vencimiento']})
        messages.success(request, 'Comprobante de homologación recuperado por consulta, sin reenviar la solicitud.')
    except FacturaCEnsayoError as exc:
        messages.warning(request, str(exc)[:240])
    except Exception:
        messages.error(request, 'No pudo completarse la consulta. La operación sigue sin poder reenviarse.')
    return redirect('marca:arca_resultado_5h')


@never_cache
@require_GET
def resultado_ensayo_c_5h(request):
    if not autorizado(request):
        return HttpResponseForbidden('Solo propietario.')
    row = ArcaEnsayoFacturaC.objects.order_by('-creado').first()
    return render(request, 'marca/ensayo_c_5h.html', {'ensayo':row})
