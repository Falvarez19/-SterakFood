"""Desktop: envíos idempotentes. Nunca muta negocios en Render."""
import json
import requests
from uuid import UUID
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from desktop6c.models import DesktopLink
from desktop6c.security import clean_server_url, decrypt_token
from .models import Desktop6eDevice, Desktop6eOutbox, Desktop6eSettings
from .protocol import VERSION, validar


class ReceptorNoListo(Exception):pass


def _datos_vinculo():
    if not getattr(settings,'STERAK_DESKTOP_MODE',False):
        raise ReceptorNoListo('Solo disponible en Desktop.')
    link=DesktopLink.objects.first()
    if not link:raise ReceptorNoListo('Vinculá primero el restaurante.')
    server=clean_server_url(link.server_url)
    token=decrypt_token(link.token_ciphertext)
    return link,server,token


def _json_response(resp):
    if len(resp.content)>16384:
        raise ReceptorNoListo('La respuesta del servidor es demasiado grande.')
    try:body=resp.json()
    except (ValueError,UnicodeError):raise ReceptorNoListo('El servidor no devolvió JSON válido.')
    if not isinstance(body,dict):raise ReceptorNoListo('Respuesta inválida.')
    return body


def comprobar_receptor():
    link,server,token=_datos_vinculo()
    with requests.get(server+'/desktop/api/v1/operaciones/',
                      headers={'Authorization':'Bearer '+token,'Accept':'application/json'},
                      timeout=(5,15),allow_redirects=False) as resp:
        if resp.status_code!=200:
            raise ReceptorNoListo(f'Receptor 6E no disponible: HTTP {resp.status_code}. Primero actualizá Render.')
        data=_json_response(resp)
    if (data.get('schema')!=VERSION or
        data.get('installation_id')!=str(link.web_instance_id) or
        data.get('operations_receiver') is not True):
        raise ReceptorNoListo('La identidad web o la versión del receptor 6E no coincide.')
    if data.get('persistent_storage') is not True:
        raise ReceptorNoListo('Render no confirmó PostgreSQL persistente. Se bloqueó el envío para evitar pérdida de ventas.')
    return True


def enviar_pendientes(limite=15, habilitacion_requerida=True):
    if not getattr(settings,'STERAK_DESKTOP_MODE',False):raise ReceptorNoListo('No es Desktop.')
    ajustes=Desktop6eSettings.objects.filter(pk=1).first()
    if habilitacion_requerida and not (ajustes and ajustes.enviar_automaticamente):
        return {'enviados':0,'pendientes':Desktop6eOutbox.objects.filter(status='pendiente').count(),'detalle':'Envío automático desactivado.'}
    comprobar_receptor()
    link,server,token=_datos_vinculo()
    device,_=Desktop6eDevice.objects.get_or_create(pk=1)
    enviados=0
    eventos=list(Desktop6eOutbox.objects.filter(status='pendiente').order_by('created_at','event_id')[:limite])
    for e in eventos:
        paquete={'schema':VERSION,'installation_id':str(link.web_instance_id),
                 'device_id':str(device.uid),'event_id':str(e.event_id),
                 'tipo':e.tipo,'origen':e.origen,'payload':e.payload,'digest':e.digest}
        validar(paquete)
        try:
            with requests.post(server+'/desktop/api/v1/operaciones/',json=paquete,
                               headers={'Authorization':'Bearer '+token,'Accept':'application/json'},
                               timeout=(5,20),allow_redirects=False) as resp:
                body=_json_response(resp)
                if resp.status_code not in (200,201):
                    raise ReceptorNoListo('Render rechazó el evento HTTP '+str(resp.status_code)+': '+str(body.get('error',''))[:90])
                if body.get('status')!='ok' or body.get('event_id')!=str(e.event_id):
                    raise ReceptorNoListo('El acuse no corresponde al evento enviado.')
            Desktop6eOutbox.objects.filter(pk=e.pk,status='pendiente').update(
                status='confirmado',acknowledged_at=timezone.now(),intentos=e.intentos+1,error='')
            enviados+=1
        except (requests.RequestException,ReceptorNoListo,ValueError) as exc:
            Desktop6eOutbox.objects.filter(pk=e.pk,status='pendiente').update(
                intentos=e.intentos+1,error=str(exc)[:240])
            # La operación queda pendiente para reintentar; no se genera un nuevo UUID.
            raise ReceptorNoListo('No se confirmó el evento '+str(e.event_id)[:8]+': '+str(exc)[:180])
    return {'enviados':enviados,'pendientes':Desktop6eOutbox.objects.filter(status='pendiente').count(),
            'detalle':'Cada evento fue confirmado por Render.'}
