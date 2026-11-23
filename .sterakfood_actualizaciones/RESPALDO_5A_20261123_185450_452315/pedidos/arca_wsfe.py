"""Cliente acotado WSAA + WSFEv1, Factura B consumidor final (homologación por defecto).

NUNCA invoca FECAESolicitar al importar este módulo. No hace llamadas reales sin
ARCA_FISCAL_ENABLED=1 y credenciales; producción exige guardia adicional.
"""
import base64
import json
import os
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from xml.etree import ElementTree as ET

import requests
from django.conf import settings
from django.core.cache import cache
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs7, pkcs12

SOAP = 'http://schemas.xmlsoap.org/soap/envelope/'
WSFE_NS = 'http://ar.gov.afip.dif.FEV1/'
WSAA_NS = 'http://wsaa.view.sua.dvadac.desein.afip.gov'
URLS = {
    'homologacion': ('https://wsaahomo.afip.gov.ar/ws/services/LoginCms', 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx'),
    'produccion': ('https://wsaa.afip.gov.ar/ws/services/LoginCms', 'https://servicios1.afip.gov.ar/wsfev1/service.asmx'),
}

class ArcaError(Exception):
    pass

class ArcaIncierto(ArcaError):
    """No se sabe si ARCA aceptó el pedido; NO reenviar automáticamente."""


def _add(parent, name, content):
    el = ET.SubElement(parent, name)
    el.text = str(content)
    return el


def _first(root, name):
    return next((n for n in root.iter() if n.tag.split('}')[-1] == name), None)


def _value(root, name, default=''):
    found = _first(root, name)
    return (found.text or '').strip() if found is not None else default


def _xml(data):
    try:
        if len(data) > 2_000_000:
            raise ArcaError('La respuesta de ARCA es demasiado grande.')
        return ET.fromstring(data)
    except ET.ParseError as exc:
        raise ArcaError('ARCA respondió un XML inválido.') from exc


def _soap_post(url, action, body_element):
    envelope = ET.Element(f'{{{SOAP}}}Envelope')
    ET.SubElement(envelope, f'{{{SOAP}}}Header')
    body = ET.SubElement(envelope, f'{{{SOAP}}}Body')
    body.append(body_element)
    payload = ET.tostring(envelope, encoding='utf-8', xml_declaration=True)
    try:
        response = requests.post(url, data=payload,
            headers={'Content-Type':'text/xml; charset=utf-8', 'SOAPAction':f'"{action}"'},
            timeout=(6, 20))
    except requests.RequestException as exc:
        # Could have been committed upstream. Callers treat a send failure as uncertain.
        raise ArcaIncierto('Sin respuesta de ARCA. Revisar comprobante antes de reenviar.') from exc
    if response.status_code != 200:
        raise ArcaIncierto(f'ARCA devolvió HTTP {response.status_code}; verificar antes de reintentar.')
    root = _xml(response.content)
    fault = _first(root, 'Fault')
    if fault is not None:
        message = _value(fault,'faultstring','Error SOAP')[:350]
        raise ArcaError('ARCA: ' + message)
    return root


def _environment():
    env = os.environ.get('ARCA_ENV', 'homologacion').strip().lower()
    if env not in URLS:
        raise ArcaError('ARCA_ENV debe ser homologacion o produccion.')
    if os.environ.get('ARCA_FISCAL_ENABLED') != '1':
        raise ArcaError('Emisión deshabilitada: configurar ARCA_FISCAL_ENABLED=1.')
    if env == 'produccion':
        if os.environ.get('ARCA_PRODUCCION_CONFIRMADA') != 'SI':
            raise ArcaError('Producción bloqueada: falta ARCA_PRODUCCION_CONFIRMADA=SI.')
        for name in ('ARCA_RAZON_SOCIAL', 'ARCA_DOMICILIO', 'ARCA_CONDICION_IVA',
                     'ARCA_INGRESOS_BRUTOS', 'ARCA_INICIO_ACTIVIDADES'):
            if not os.environ.get(name, '').strip():
                raise ArcaError('Falta información del emisor para la ticketera: ' + name)
    return env


def _credentials():
    raw = os.environ.get('ARCA_P12_BASE64','').strip()
    pwd = os.environ.get('ARCA_P12_PASSWORD','')
    if not raw:
        raise ArcaError('Falta ARCA_P12_BASE64 (certificado para el entorno configurado).')
    try:
        binary = base64.b64decode(raw, validate=True)
        key, cert, others = pkcs12.load_key_and_certificates(binary, pwd.encode() if pwd else None)
    except Exception as exc:
        raise ArcaError('No se pudo abrir el certificado P12. Revisar archivo y contraseña.') from exc
    if key is None or cert is None:
        raise ArcaError('El P12 debe incluir certificado y clave privada.')
    now = datetime.now(timezone.utc)
    expiry = getattr(cert,'not_valid_after_utc', cert.not_valid_after.replace(tzinfo=timezone.utc))
    if expiry < now:
        raise ArcaError('Certificado digital vencido.')
    return key, cert


def _get_token(env):
    # No almacenar claves privadas ni certificados en DB o logs.
    wsaa_url, _ = URLS[env]
    cuit = os.environ.get('ARCA_CUIT','').strip()
    if not cuit.isdigit() or len(cuit) != 11:
        raise ArcaError('Configurar ARCA_CUIT con 11 dígitos.')
    cache_key = f'arca_wsaa_wsfe_{env}_{cuit}'
    cached = cache.get(cache_key)
    if cached:
        return cached
    key, cert = _credentials()
    now = datetime.now(timezone.utc)
    tra = ET.Element('loginTicketRequest',version='1.0')
    header = ET.SubElement(tra,'header')
    _add(header,'uniqueId', int(time.time()) % 2147483647)
    _add(header,'generationTime',(now-timedelta(minutes=10)).isoformat(timespec='seconds'))
    _add(header,'expirationTime',(now+timedelta(minutes=10)).isoformat(timespec='seconds'))
    _add(tra,'service','wsfe')
    cms = pkcs7.PKCS7SignatureBuilder().set_data(ET.tostring(tra,encoding='utf-8',xml_declaration=True))
    cms = cms.add_signer(cert,key,hashes.SHA256()).sign(serialization.Encoding.DER,[pkcs7.PKCS7Options.Binary])
    login = ET.Element(f'{{{WSAA_NS}}}loginCms')
    _add(login, f'{{{WSAA_NS}}}in0', base64.b64encode(cms).decode('ascii'))
    response = _soap_post(wsaa_url, '', login)
    result = _value(response, 'loginCmsReturn')
    if not result:
        raise ArcaError('WSAA no devolvió ticket de acceso.')
    ticket = _xml(result.encode('utf-8'))
    token, sign = _value(ticket,'token'), _value(ticket,'sign')
    if not token or not sign:
        raise ArcaError('WSAA no devolvió Token y Sign.')
    data = (token,sign,cuit)
    # Cache 8 min < 10 min de validez del TRA; el TA suele tener mayor validez.
    cache.set(cache_key,data,timeout=480)
    return data


def _request(operation, fields=None, auth=True):
    env = _environment()
    _, wsfe_url = URLS[env]
    root = ET.Element(f'{{{WSFE_NS}}}{operation}')
    if auth:
        token, sign, cuit = _get_token(env)
        node = ET.SubElement(root, f'{{{WSFE_NS}}}Auth')
        for key,val in [('Token',token),('Sign',sign),('Cuit',cuit)]:
            _add(node, f'{{{WSFE_NS}}}{key}', val)
    if fields:
        for k,v in fields.items():
            _add(root, f'{{{WSFE_NS}}}{k}', v)
    response = _soap_post(wsfe_url, WSFE_NS + operation, root)
    errors = _first(response,'Errors')
    messages = []
    if errors is not None:
        for err in errors:
            code = _value(err,'Code')
            msg = _value(err,'Msg')
            if code or msg: messages.append(f'{code}: {msg}'[:250])
    if messages:
        raise ArcaError('ARCA rechazó la consulta: ' + '; '.join(messages)[:500])
    return response


def ultimo_autorizado(pv, tipo=6):
    root = _request('FECompUltimoAutorizado', {'PtoVta':pv,'CbteTipo':tipo})
    n = _value(root,'CbteNro')
    if not n.isdigit(): raise ArcaError('ARCA no devolvió el último número autorizado.')
    return int(n)


def consultar(pv,tipo,numero):
    env = _environment()
    _, url = URLS[env]
    token, sign, cuit = _get_token(env)
    op = ET.Element(f'{{{WSFE_NS}}}FECompConsultar')
    auth = ET.SubElement(op,f'{{{WSFE_NS}}}Auth')
    for key, val in [('Token',token),('Sign',sign),('Cuit',cuit)]: _add(auth,f'{{{WSFE_NS}}}{key}',val)
    req = ET.SubElement(op,f'{{{WSFE_NS}}}FeCompConsReq')
    for key, val in [('CbteTipo',tipo),('CbteNro',numero),('PtoVta',pv)]: _add(req,f'{{{WSFE_NS}}}{key}',val)
    root = _soap_post(url,WSFE_NS+'FECompConsultar',op)
    result = _first(root,'ResultGet')
    if result is None:
        return None
    cae = _value(result,'CodAutorizacion')
    if not cae: return None
    return {'cae':cae,'vencimiento':_value(result,'FchVto'),'total':_value(result,'ImpTotal'),
            'fecha':_value(result,'CbteFch'),'numero':int(numero)}


def emitir_factura_b(pv,numero,importe, fecha, iva_receptor=5):
    """Factura B de bienes gravados al 21%, receptor Consumidor Final.

    No usar para otras alícuotas/exenciones/servicios sin ampliar reglas fiscales.
    """
    env = _environment()
    _, url = URLS[env]
    token, sign, cuit = _get_token(env)
    importe = Decimal(str(importe)).quantize(Decimal('0.01'))
    if importe <= 0 or importe >= Decimal('9999999999'):
        raise ArcaError('Importe fuera de rango.')
    neto = (importe / Decimal('1.21')).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    iva = importe - neto
    op = ET.Element(f'{{{WSFE_NS}}}FECAESolicitar')
    auth = ET.SubElement(op, f'{{{WSFE_NS}}}Auth')
    for k,v in [('Token',token),('Sign',sign),('Cuit',cuit)]: _add(auth,f'{{{WSFE_NS}}}{k}',v)
    req = ET.SubElement(op,f'{{{WSFE_NS}}}FeCAEReq')
    cab = ET.SubElement(req,f'{{{WSFE_NS}}}FeCabReq')
    for k,v in [('CantReg',1),('PtoVta',pv),('CbteTipo',6)]: _add(cab,f'{{{WSFE_NS}}}{k}',v)
    details = ET.SubElement(req,f'{{{WSFE_NS}}}FeDetReq')
    detail = ET.SubElement(details,f'{{{WSFE_NS}}}FECAEDetRequest')
    values = [('Concepto',1),('DocTipo',99),('DocNro',0),('CbteDesde',numero),('CbteHasta',numero),
              ('CbteFch',fecha),('ImpTotal',importe),('ImpTotConc','0.00'),('ImpNeto',neto),
              ('ImpOpEx','0.00'),('ImpTrib','0.00'),('ImpIVA',iva),('MonId','PES'),('MonCotiz',1)]
    for k,v in values: _add(detail,f'{{{WSFE_NS}}}{k}',v)
    tax = ET.SubElement(detail,f'{{{WSFE_NS}}}Iva')
    taxrow = ET.SubElement(tax,f'{{{WSFE_NS}}}AlicIva')
    for k,v in [('Id',5),('BaseImp',neto),('Importe',iva)]: _add(taxrow,f'{{{WSFE_NS}}}{k}',v)
    # Campo incorporado en la versión reciente de WSFEv1; conservarlo
    # tras los nodos tradicionales de detalle/IVA.
    _add(detail, f'{{{WSFE_NS}}}CondicionIVAReceptorId', iva_receptor)
    root = _soap_post(url,WSFE_NS+'FECAESolicitar',op)
    header = _first(root,'FeCabResp')
    detail_resp = _first(root,'FECAEDetResponse')
    if detail_resp is None:
        raise ArcaIncierto('Respuesta de ARCA sin detalle: verificar antes de reintentar.')
    cae, venc = _value(detail_resp,'CAE'), _value(detail_resp,'CAEFchVto')
    resultado = _value(detail_resp,'Resultado')
    if resultado != 'A' or not cae or not venc:
        observations=[]
        obs = _first(detail_resp,'Observaciones')
        if obs is not None:
            observations=[f"{_value(x,'Code')}: {_value(x,'Msg')}"[:180] for x in obs]
        if resultado == 'R':
            raise ArcaError('ARCA rechazó el comprobante. ' + '; '.join(observations)[:450])
        raise ArcaIncierto('La respuesta fiscal no confirma autorización. Consultar antes de reintentar.')
    return {'numero':int(numero),'cae':cae,'vencimiento':venc,'total':str(importe),
            'neto':str(neto),'iva':str(iva),'fecha':fecha}


def url_qr(cuit,pv,numero,fecha,importe,cae):
    value = {'ver':1,'fecha':f'{fecha[:4]}-{fecha[4:6]}-{fecha[6:8]}',
             'cuit':int(cuit),'ptoVta':int(pv),'tipoCmp':6,'nroCmp':int(numero),
             'importe':float(importe),'moneda':'PES','ctz':1,
             'tipoDocRec':99,'nroDocRec':0,'tipoCodAut':'E','codAut':int(cae)}
    return 'https://www.arca.gob.ar/fe/qr/?p=' + base64.b64encode(json.dumps(value,separators=(',',':')).encode()).decode()
