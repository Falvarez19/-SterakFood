"""Paso 5G: prevalidación solo lectura de Factura C en homologación.

No emite comprobantes, no cambia activación fiscal ni accede a producción.
Solo dueño del negocio; en errores jamás expone Token, Sign o contraseñas.
"""
from __future__ import annotations

from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from .views import autorizado


def verificar_preflight_c():
    from pedidos.models import ConfiguracionFiscal
    from .models import ArcaCredencial
    from .arca_vault_5a import cargar_runtime, consultar_puntos, _token_wsaa
    from .arca_diagnostico_4f import _fedummy, _punto_valido
    from pedidos.arca_wsfe import URLS, _soap_post
    from pedidos.arca_c_consulta_5g import armar_ultimo_c, leer_ultimo_c, WSFE_NS

    fiscal = ConfiguracionFiscal.objects.filter(pk=1).first()
    if fiscal is None or fiscal.condicion_iva != 'monotributo':
        raise ValueError('Para verificar Factura C, los Datos fiscales deben corresponder a un monotributista.')
    if not fiscal.cuit or len(fiscal.cuit) != 11 or not fiscal.cuit.isdigit():
        raise ValueError('Primero configurá un CUIT válido en Datos fiscales.')
    pv = fiscal.punto_venta_referencia
    if type(pv) is not int or not 1 <= pv <= 99999:
        raise ValueError('Primero configurá el punto de venta en Datos fiscales.')
    row = ArcaCredencial.objects.filter(entorno='homologacion').first()
    if row is None:
        raise ValueError('Falta cargar desde Mi negocio un certificado de homologación.')
    if row.cuit != fiscal.cuit or row.punto_venta != pv:
        raise ValueError('El certificado no coincide con CUIT o punto de venta. Revisá los Datos fiscales.')
    if not _fedummy('homologacion').get('disponible', False):
        raise ValueError('Los servidores de homologación de ARCA no están disponibles.')
    runtime = cargar_runtime(row)
    if runtime.entorno != 'homologacion':
        raise ValueError('Se bloqueó una credencial de producción en una prueba de homologación.')
    puntos = consultar_puntos(runtime)  # Solo FEParamGetPtosVenta
    encontrado = next((x for x in puntos if x['numero'] == pv), None)
    if not encontrado:
        raise ValueError('ARCA no devolvió este punto de venta para el emisor en homologación.')
    ok, _detalle = _punto_valido(encontrado)
    if not ok:
        raise ValueError('El punto de venta no figura activo para CAE en homologación.')
    token, sign, cuit = _token_wsaa(runtime)  # Sesión WSAA, sin emisión
    body = armar_ultimo_c(token, sign, cuit, pv, entorno=runtime.entorno)
    response = _soap_post(URLS['homologacion'][1], WSFE_NS+'FECompUltimoAutorizado', body)
    ultimo = leer_ultimo_c(response)
    return {'ultimo': ultimo, 'punto_venta': pv}


@never_cache
@csrf_protect
@require_POST
def preflight_factura_c_5g(request):
    if not autorizado(request):
        return HttpResponseForbidden('Acceso exclusivo del propietario.')
    try:
        resultado = verificar_preflight_c()
    except ValueError as exc:
        # Errores de validación propios (nunca incluyen secretos).
        messages.warning(request, str(exc)[:240])
    except Exception:
        # No publicar trazas de servicios SOAP, certificados ni rutas internas.
        messages.error(request, 'No se completó la consulta de Factura C en homologación. Revisá certificado, permisos y conexión con ARCA.')
    else:
        messages.success(request,
            'Factura C (tipo 11): consulta de solo lectura correcta en homologación. '
            f'Último número informado para PV {resultado["punto_venta"]:05d}: {resultado["ultimo"]}. '
            'No se emitió factura, no se pidió CAE y la emisión sigue bloqueada.')
    return redirect('marca:arca_propietario')
