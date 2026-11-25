"""SterakFood 5A: bóveda fiscal por instalación. No guarda secretos en logs/disco.

Cada despliegue de SterakFood corresponde a un negocio/una base de datos.
El operador de la plataforma debe aprovisionar UNA clave Fernet estable mediante
STERAK_ARCA_VAULT_KEY y respaldarla separadamente de la base de datos.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree as ET

from cryptography import x509
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs7, pkcs12
from django.core.cache import cache
from django.db.utils import OperationalError, ProgrammingError

MAX_P12_BYTES = 256 * 1024
FE_NS = 'http://ar.gov.afip.dif.FEV1/'


from pedidos.arca_wsfe import ArcaError


class ConfiguracionSeguraError(ArcaError):
    pass


def _fernet():
    raw = os.environ.get('STERAK_ARCA_VAULT_KEY', '').strip()
    if not raw:
        raise ConfiguracionSeguraError(
            'Falta habilitar la bóveda cifrada. El administrador debe configurar STERAK_ARCA_VAULT_KEY una sola vez.'
        )
    try:
        return Fernet(raw.encode('ascii'))
    except (ValueError, TypeError, UnicodeError) as exc:
        raise ConfiguracionSeguraError('La clave de cifrado del servidor no tiene un formato válido.') from exc


def boveda_disponible():
    try:
        _fernet()
    except ConfiguracionSeguraError:
        return False
    return True


def cifrar_archivo(archivo, password):
    if not 0 < len(archivo) <= MAX_P12_BYTES:
        raise ConfiguracionSeguraError('El certificado debe tener entre 1 byte y 256 KB.')
    if len(password) > 250:
        raise ConfiguracionSeguraError('La contraseña es demasiado larga.')
    data = json.dumps({
        'p12': base64.b64encode(archivo).decode('ascii'),
        'password': password,
    }, separators=(',', ':')).encode('utf-8')
    return _fernet().encrypt(data)


def _descifrar(row):
    try:
        payload = json.loads(_fernet().decrypt(bytes(row.secreto_cifrado)))
        return base64.b64decode(payload['p12'], validate=True), payload['password']
    except (InvalidToken, ValueError, TypeError, KeyError, UnicodeError, json.JSONDecodeError) as exc:
        raise ConfiguracionSeguraError('No se pudo descifrar el certificado: verificá la clave de la bóveda y su respaldo.') from exc


def _vigencia(cert):
    inicio = getattr(cert, 'not_valid_before_utc', None) or cert.not_valid_before.replace(tzinfo=timezone.utc)
    fin = getattr(cert, 'not_valid_after_utc', None) or cert.not_valid_after.replace(tzinfo=timezone.utc)
    ahora = datetime.now(timezone.utc)
    if ahora < inicio:
        raise ConfiguracionSeguraError('El certificado todavía no está vigente.')
    if ahora >= fin:
        raise ConfiguracionSeguraError('El certificado digital está vencido.')
    return fin


def abrir_p12(binary, password):
    if not binary or len(binary) > MAX_P12_BYTES:
        raise ConfiguracionSeguraError('El certificado P12 está vacío o supera 256 KB.')
    try:
        key, cert, _others = pkcs12.load_key_and_certificates(
            binary, password.encode('utf-8') if password else None)
    except (TypeError, ValueError) as exc:
        raise ConfiguracionSeguraError('El P12 no se pudo abrir: revisá el archivo y la contraseña.') from exc
    if key is None or cert is None:
        raise ConfiguracionSeguraError('El P12 debe contener el certificado y su clave privada.')
    fin = _vigencia(cert)
    huella = cert.fingerprint(hashes.SHA256()).hex()
    return key, cert, fin, huella


@dataclass(frozen=True)
class RuntimeFiscal:
    entorno: str
    cuit: str
    punto_venta: int
    clave_privada: object
    certificado: x509.Certificate
    huella: str


def cargar_runtime(row):
    binary, password = _descifrar(row)
    key, cert, _fin, huella = abrir_p12(binary, password)
    if huella != row.huella_sha256:
        raise ConfiguracionSeguraError('El certificado almacenado no coincide con el validado.')
    return RuntimeFiscal(row.entorno, row.cuit, row.punto_venta, key, cert, huella)


def credencial_activa():
    from .models import ArcaCredencial
    try:
        return ArcaCredencial.objects.filter(activa=True).first()
    except (OperationalError, ProgrammingError):
        return None  # Código instalado, migración aún pendiente: modo legado.


def runtime_emision():
    """Una credencial cargada pero NO activada bloquea la emisión legada.

    No permitimos que el botón 'Desactivar' parezca efectivo si todavía hay
    variables heredadas ARCA_FISCAL_ENABLED=1 en el servidor.
    """
    from .models import ArcaCredencial
    try:
        row = ArcaCredencial.objects.filter(activa=True).first()
        if row is None:
            # STERAKFOOD_5B_BLOQUEO_EMISION_LEGADA
            # No permitir facturar por variables antiguas del servidor.
            # Una credencial debe validarse y activarse desde Mi negocio.
            raise ConfiguracionSeguraError(
                'La facturación está deshabilitada. Cargá, verificá y activá el certificado desde Mi negocio.'
            )
    except (OperationalError, ProgrammingError):
        return None
    from pedidos.models import ConfiguracionFiscal
    fiscal = ConfiguracionFiscal.objects.filter(pk=1).first()
    if fiscal is None or fiscal.cuit != row.cuit or fiscal.punto_venta_referencia != row.punto_venta or fiscal.condicion_iva != 'ri':
        raise ConfiguracionSeguraError('Datos fiscales cambiados: verificá y activá nuevamente desde Mi negocio.')
    return cargar_runtime(row)


def invalidar_por_cambio_fiscal():
    from .models import ArcaCredencial
    try:
        ArcaCredencial.objects.all().update(activa=False, verificada=False)
    except (OperationalError, ProgrammingError):
        pass


def _token_wsaa(runtime, *, usar_cache=True):
    """Solicita TA de lectura y emisión; no solicita CAE."""
    from pedidos.arca_wsfe import URLS, WSAA_NS, _soap_post, _value, _xml
    env = runtime.entorno
    if env not in URLS:
        raise ConfiguracionSeguraError('Entorno ARCA no permitido.')
    cache_key = 'sterak_arca_5a_wsaa_' + hashlib.sha256(
        (runtime.entorno + ':' + runtime.cuit + ':' + runtime.huella).encode()).hexdigest()
    if usar_cache:
        result = cache.get(cache_key)
        if result:
            return result
    ahora = datetime.now(timezone.utc)
    tra = ET.Element('loginTicketRequest', version='1.0')
    header = ET.SubElement(tra, 'header')
    ET.SubElement(header, 'uniqueId').text = str(int(time.time()) % 2147483647)
    ET.SubElement(header, 'generationTime').text = (ahora-timedelta(minutes=10)).isoformat(timespec='seconds')
    ET.SubElement(header, 'expirationTime').text = (ahora+timedelta(minutes=10)).isoformat(timespec='seconds')
    ET.SubElement(tra, 'service').text = 'wsfe'
    cms = pkcs7.PKCS7SignatureBuilder().set_data(ET.tostring(tra, encoding='utf-8', xml_declaration=True))
    cms = cms.add_signer(runtime.certificado, runtime.clave_privada, hashes.SHA256())
    data = cms.sign(serialization.Encoding.DER, [pkcs7.PKCS7Options.Binary])
    nodo = ET.Element(f'{{{WSAA_NS}}}loginCms')
    ET.SubElement(nodo, f'{{{WSAA_NS}}}in0').text = base64.b64encode(data).decode('ascii')
    respuesta = _soap_post(URLS[env][0], '', nodo)
    ticket_cms = _value(respuesta, 'loginCmsReturn')
    if not ticket_cms:
        raise ConfiguracionSeguraError('ARCA no entregó un ticket WSAA.')
    ticket = _xml(ticket_cms.encode('utf-8'))
    token, firma = _value(ticket, 'token'), _value(ticket, 'sign')
    if not token or not firma:
        raise ConfiguracionSeguraError('El ticket WSAA no contiene token y firma.')
    resultado = token, firma, runtime.cuit
    cache.set(cache_key, resultado, timeout=480)
    return resultado


def token_runtime_emision(runtime):
    return _token_wsaa(runtime)


def consultar_puntos(runtime):
    from pedidos.arca_wsfe import URLS, _soap_post
    from .arca_diagnostico_4f import _datos_puntos
    token, firma, cuit = _token_wsaa(runtime, usar_cache=False)
    op = ET.Element(f'{{{FE_NS}}}FEParamGetPtosVenta')
    auth = ET.SubElement(op, f'{{{FE_NS}}}Auth')
    for nombre, valor in (('Token', token), ('Sign', firma), ('Cuit', cuit)):
        ET.SubElement(auth, f'{{{FE_NS}}}{nombre}').text = str(valor)
    respuesta = _soap_post(URLS[runtime.entorno][1], FE_NS + 'FEParamGetPtosVenta', op)
    return _datos_puntos(respuesta)


def verificar_row(row, fiscal):
    from .arca_diagnostico_4f import _fedummy, _punto_valido
    if not fiscal.cuit or fiscal.cuit != row.cuit or fiscal.punto_venta_referencia != row.punto_venta:
        raise ConfiguracionSeguraError('Guardá primero el mismo CUIT y punto de venta en Datos fiscales.')
    if fiscal.condicion_iva != 'ri':
        raise ConfiguracionSeguraError(
            'El emisor actual solo soporta Factura B con productos íntegramente al 21% de IVA. '
            'No habilitar para monotributo/exentos antes de incorporar Factura C y sus reglas.'
        )
    if not fiscal.razon_social or not fiscal.domicilio_fiscal:
        raise ConfiguracionSeguraError('Completá razón social y domicilio fiscal.')
    if not row.ingresos_brutos or not row.inicio_actividades:
        raise ConfiguracionSeguraError('Completá Ingresos Brutos e inicio de actividades para la impresión fiscal.')
    estado = _fedummy(row.entorno)
    if not estado.get('disponible'):
        raise ConfiguracionSeguraError('Los servidores ARCA no respondieron correctamente.')
    runtime = cargar_runtime(row)
    puntos = consultar_puntos(runtime)
    match = next((p for p in puntos if p['numero'] == row.punto_venta), None)
    if match is None:
        raise ConfiguracionSeguraError('El punto de venta no figura autorizado para el CUIT de este certificado.')
    correcto, razon = _punto_valido(match)
    if not correcto:
        raise ConfiguracionSeguraError('El punto de venta no está habilitado para CAE: ' + razon)
    return True


def emisor_operativo():
    runtime = runtime_emision()
    return (runtime.cuit, runtime.punto_venta) if runtime else None


def metadatos_ticket_5a():
    row = credencial_activa()
    if not row:
        return None
    from pedidos.models import ConfiguracionFiscal
    fiscal = ConfiguracionFiscal.objects.filter(pk=1).first()
    if fiscal is None:
        return None
    return {
        'razon_social': fiscal.razon_social, 'domicilio': fiscal.domicilio_fiscal,
        'condicion_iva_emisor': fiscal.get_condicion_iva_display(),
        'ingresos_brutos': row.ingresos_brutos, 'inicio_actividades': row.inicio_actividades,
    }


def estado_lectura_5a():
    from .models import ArcaCredencial
    try:
        filas = list(ArcaCredencial.objects.order_by('entorno'))
    except (OperationalError, ProgrammingError):
        return []
    return [{
        'entorno': row.entorno, 'cuit': row.cuit,
        'punto_venta': row.punto_venta, 'archivo': row.nombre_archivo,
        'vence': row.vencimiento, 'verificada': row.verificada,
        'activa': row.activa, 'ultimo_chequeo': row.ultimo_chequeo,
    } for row in filas]


def diagnostico_autogestion_5a():
    """Diagnóstico 4F para un certificado de Mi negocio. Nunca emite facturas."""
    from .models import ArcaCredencial
    from .arca_diagnostico_4f import _fedummy, _punto_valido, _paso
    try:
        row = ArcaCredencial.objects.filter(activa=True).first()
        if row is None:
            row = ArcaCredencial.objects.order_by('-actualizado').first()
    except (OperationalError, ProgrammingError):
        return None
    if not row:
        return None

    pasos = {
        'servidores': _paso('Servidores ARCA', 'pendiente', 'Esperando comprobación.'),
        'certificado': _paso('Certificado digital P12', 'pendiente', 'Esperando comprobación.'),
        'wsaa': _paso('Autenticación WSAA', 'pendiente', 'Esperando comprobación.'),
        'wsfe': _paso('Comunicación WSFEv1', 'pendiente', 'Esperando comprobación.'),
        'punto': _paso('Punto de venta', 'pendiente', 'Esperando comprobación.'),
    }
    try:
        ping = _fedummy(row.entorno)
        estados = ping.get('estados') or {}
        texto = ' · '.join(k+': '+estados.get(k, '?') for k in ('AppServer','DbServer','AuthServer'))
        pasos['servidores'] = _paso('Servidores ARCA', 'ok' if ping.get('disponible') else 'aviso', texto)
    except Exception:
        pasos['servidores'] = _paso('Servidores ARCA', 'error', 'No respondió FEDummy.')
    try:
        runtime = cargar_runtime(row)
        fin = getattr(runtime.certificado, 'not_valid_after_utc', None)
        fin = fin or runtime.certificado.not_valid_after.replace(tzinfo=timezone.utc)
        pasos['certificado'] = _paso('Certificado digital P12', 'ok', 'P12 vigente hasta ' + fin.strftime('%d/%m/%Y'))
    except Exception:
        pasos['certificado'] = _paso('Certificado digital P12', 'error', 'No se pudo abrir el certificado cifrado.')
        return {'entorno': row.entorno, 'resultado':'parcial', 'pasos':pasos,
                'mensaje':'La conexión fiscal está incompleta; no se emitieron facturas.', 'comprobante_emitido':False}
    try:
        # El TA puede reutilizarse dentro de la consulta autenticada; esta prueba
        # es deliberadamente solo lectura y no llama a FECAESolicitar.
        _token_wsaa(runtime, usar_cache=False)
        pasos['wsaa'] = _paso('Autenticación WSAA', 'ok', 'ARCA autorizó el acceso WSAA.')
    except Exception:
        pasos['wsaa'] = _paso('Autenticación WSAA', 'error', 'ARCA no autorizó WSAA. Revisá vínculo del certificado.')
        return {'entorno': row.entorno, 'resultado':'parcial', 'pasos':pasos,
                'mensaje':'La conexión fiscal está incompleta; no se emitieron facturas.', 'comprobante_emitido':False}
    try:
        puntos = consultar_puntos(runtime)
        pasos['wsfe'] = _paso('Comunicación WSFEv1', 'ok', 'ARCA respondió FEParamGetPtosVenta.')
        match = next((p for p in puntos if p['numero'] == row.punto_venta), None)
        if match:
            valido, razon = _punto_valido(match)
            pasos['punto'] = _paso('Punto de venta', 'ok' if valido else 'aviso', razon)
        else:
            pasos['punto'] = _paso('Punto de venta', 'error', 'No figura el punto configurado.')
    except Exception:
        pasos['wsfe'] = _paso('Comunicación WSFEv1', 'error', 'No se pudo consultar WSFEv1 con este certificado.')
    estado = 'ok' if all(p['estado'] == 'ok' for p in pasos.values()) else 'parcial'
    return {'entorno':row.entorno, 'resultado':estado, 'pasos':pasos,
            'mensaje':'Diagnóstico finalizado. No se emitieron facturas.', 'comprobante_emitido':False}
