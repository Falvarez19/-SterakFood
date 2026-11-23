"""Diagnostico de lectura ARCA, 4F. Nunca emite comprobantes ni cambia credenciales."""
from __future__ import annotations

import os
from xml.etree import ElementTree as ET

from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from .arca_certificado_4g import inspeccionar_certificado  # STERAKFOOD_4G_CERTIFICADO_INTEGRADO
from .views import autorizado


FE_NS = 'http://ar.gov.afip.dif.FEV1/'


def _paso(nombre, estado, detalle):
    return {'nombre': nombre, 'estado': estado, 'detalle': detalle}


def _valor(elemento, nombre):
    # El namespace exacto del servidor puede variar entre mensajes SOAP.
    for nodo in elemento.iter():
        if nodo.tag.split('}')[-1] == nombre:
            return (nodo.text or '').strip()
    return ''


def _errores_wsfe(root):
    for nodo in root.iter():
        if nodo.tag.split('}')[-1] == 'Errors':
            return bool(list(nodo))
    return False


def _datos_puntos(root):
    """Extrae solo datos operativos de FEParamGetPtosVentaResult."""
    resultado = next((n for n in root.iter()
                      if n.tag.split('}')[-1] == 'FEParamGetPtosVentaResult'), None)
    if resultado is None:
        raise ValueError('WSFEv1 no devolvió la estructura esperada.')
    if _errores_wsfe(resultado):
        raise ValueError('ARCA rechazó la consulta de puntos de venta. Revisá permisos WSFEv1.')
    puntos = []
    for nodo in resultado.iter():
        if nodo.tag.split('}')[-1] == 'PtoVenta':
            numero = _valor(nodo, 'Nro')
            if numero.isdigit():
                puntos.append({
                    'numero': int(numero),
                    'emision': _valor(nodo, 'EmisionTipo').upper(),
                    'bloqueado': _valor(nodo, 'Bloqueado').upper(),
                    'fecha_baja': _valor(nodo, 'FchBaja'),
                })
    return puntos


def _punto_valido(p):
    if p['bloqueado'] == 'S' or p['fecha_baja'] not in ('', '00000000'):
        return False, 'El punto de venta figura bloqueado o dado de baja.'
    if p['bloqueado'] != 'N':
        return False, 'ARCA no confirmó que el punto de venta esté desbloqueado.'
    if p['emision'] != 'CAE':
        return False, 'El punto de venta no figura con modalidad CAE.'
    return True, 'Punto de venta activo, sin bloqueo y con modalidad CAE.'


def _fedummy(env):
    if env == 'homologacion':
        from pedidos.arca_homologacion import fedummy_homologacion
        return fedummy_homologacion()
    from pedidos.arca_wsfe import URLS, _soap_post
    _, url = URLS[env]
    root = _soap_post(url, FE_NS + 'FEDummy', ET.Element(f'{{{FE_NS}}}FEDummy'))
    estados = {key: _valor(root, key) for key in ('AppServer', 'DbServer', 'AuthServer')}
    if not all(estados.values()):
        raise ValueError('ARCA devolvió una respuesta FEDummy incompleta.')
    return {'disponible': all(v.upper() == 'OK' for v in estados.values()), 'estados': estados}


def _puntos_autenticados(env):
    """Solo lectura: autentica WSAA y consulta FEParamGetPtosVenta en WSFEv1."""
    from pedidos.arca_wsfe import URLS, _get_token, _soap_post
    # No llamar a _environment: esa funcion bloquea la emisión; diagnóstico es independiente.
    token, firma, cuit = _get_token(env)
    root = ET.Element(f'{{{FE_NS}}}FEParamGetPtosVenta')
    auth = ET.SubElement(root, f'{{{FE_NS}}}Auth')
    for nombre, valor in (('Token', token), ('Sign', firma), ('Cuit', cuit)):
        node = ET.SubElement(auth, f'{{{FE_NS}}}{nombre}')
        node.text = str(valor)
    _, url = URLS[env]
    respuesta = _soap_post(url, FE_NS + 'FEParamGetPtosVenta', root)
    return _datos_puntos(respuesta)


@never_cache
@csrf_protect
@require_POST
def diagnosticar_arca(request):
    """Exclusivo de propietario, con CSRF gestionado por Django. No solicita CAE."""
    if not autorizado(request):
        return JsonResponse({'error': 'Acceso exclusivo del propietario.'}, status=403)

    env = os.environ.get('ARCA_ENV', 'homologacion').strip().lower()
    pasos = {
        'certificado': _paso('Certificado digital P12', 'pendiente', 'Todavía no se comprobó.'),
        'servidores': _paso('Servidores ARCA', 'pendiente', 'Todavía no se comprobaron.'),
        'wsaa': _paso('Autenticación WSAA', 'pendiente', 'Requiere certificado y CUIT.'),
        'wsfe': _paso('Consulta WSFEv1', 'pendiente', 'Requiere autenticación.'),
        'punto': _paso('Punto de venta', 'pendiente', 'Requiere consulta WSFEv1.'),
    }
    if env not in ('homologacion', 'produccion'):
        pasos['servidores'] = _paso('Servidores ARCA', 'error', 'ARCA_ENV debe ser homologacion o produccion.')
        return JsonResponse({'entorno': 'sin configurar', 'resultado': 'error', 'pasos': pasos,
                             'mensaje': 'Configuración ARCA_ENV inválida. No se emitieron comprobantes.'})

    try:
        status = _fedummy(env)
        estados = status.get('estados', {})
        detalle = ' · '.join(f'{key}: {estados.get(key, "?")}'
                             for key in ('AppServer', 'DbServer', 'AuthServer'))
        pasos['servidores'] = _paso('Servidores ARCA', 'ok' if status['disponible'] else 'aviso', detalle)
    except Exception:
        # No publicar respuestas SOAP internas ni secretos en JSON.
        pasos['servidores'] = _paso('Servidores ARCA', 'error', 'No respondió el servicio FEDummy; reintentá más tarde.')

    estado_cert = inspeccionar_certificado()
    pasos['certificado'] = _paso('Certificado digital P12', estado_cert['estado'], estado_cert['detalle'])
    cuit = os.environ.get('ARCA_CUIT', '').strip()
    cert = bool(os.environ.get('ARCA_P12_BASE64', '').strip())
    pv_raw = os.environ.get('ARCA_PUNTO_VENTA', '').strip()

    if not cert or len(cuit) != 11 or not cuit.isascii() or not cuit.isdigit():
        pasos['wsaa'] = _paso('Autenticación WSAA', 'pendiente',
                             'Falta configurar ARCA_P12_BASE64 y/o ARCA_CUIT en el servidor.')
    else:
        try:
            # Primer paso: prueba de obtención del TA; _get_token usa la caché existente.
            from pedidos.arca_wsfe import _get_token
            _get_token(env)
        except Exception:
            pasos['wsaa'] = _paso('Autenticación WSAA', 'error',
                                 'No se obtuvo autorización WSAA. Revisá certificado, contraseña, CUIT y permisos.')
        else:
            pasos['wsaa'] = _paso('Autenticación WSAA', 'ok', 'Ticket de acceso WSAA disponible (puede estar en caché).')
            try:
                puntos = _puntos_autenticados(env)
            except Exception:
                pasos['wsfe'] = _paso('Consulta WSFEv1', 'error',
                                     'No se pudieron consultar puntos de venta en WSFEv1. Revisá permisos o conectividad.')
            else:
                pasos['wsfe'] = _paso('Consulta WSFEv1', 'ok',
                                     'ARCA respondió a FEParamGetPtosVenta, sin emitir facturas.')
                if not pv_raw.isdigit() or not 1 <= int(pv_raw) <= 99999:
                    pasos['punto'] = _paso('Punto de venta', 'pendiente',
                                          'Falta configurar ARCA_PUNTO_VENTA en el servidor.')
                else:
                    buscado = next((p for p in puntos if p['numero'] == int(pv_raw)), None)
                    if buscado is None:
                        pasos['punto'] = _paso('Punto de venta', 'aviso',
                                             f'El punto {int(pv_raw):04d} no figura en la consulta del CUIT configurado.')
                    else:
                        valido, razon = _punto_valido(buscado)
                        pasos['punto'] = _paso('Punto de venta', 'ok' if valido else 'aviso',
                                             f'Punto {int(pv_raw):04d}: {razon}')

    valores = [p['estado'] for p in pasos.values()]
    if all(v == 'ok' for v in valores):
        global_status = 'ok'
        mensaje = 'Diagnóstico técnico correcto. No habilita por sí solo la emisión fiscal.'
    elif pasos['servidores']['estado'] == 'error' and pasos['wsaa']['estado'] == 'error':
        global_status = 'error'
        mensaje = 'Fallas de conectividad/autenticación. No se emitieron facturas.'
    else:
        global_status = 'parcial'
        mensaje = 'Comprobación parcial. Revisá las indicaciones; no se emitieron facturas.'

    return JsonResponse({'entorno': env, 'resultado': global_status, 'pasos': pasos,
                         'mensaje': mensaje, 'comprobante_emitido': False})
