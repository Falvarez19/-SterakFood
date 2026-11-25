"""Render: recibe eventos POS como libro ESPEJO. No crea Pedido ni cobra."""
import json
from uuid import UUID
from django.conf import settings
from django.db import IntegrityError, transaction, connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from desktop6c.api import _authenticate, _denied
from desktop6c.models import WebInstallation
from .models import Desktop6eInbox
from .protocol import VERSION, canonical, validar


def _respuesta(data, status=200):
    r=JsonResponse(data,status=status)
    r['Cache-Control']='no-store'
    r['X-Content-Type-Options']='nosniff'
    return r


@csrf_exempt
@never_cache
@require_http_methods(['GET','POST'])
def operaciones(request):
    if getattr(settings,'STERAK_DESKTOP_MODE',False):
        return _respuesta({'error':'La API de recepción solo funciona en Render.'},404)
    credencial=_authenticate(request)
    if not credencial: return _denied()
    web,_=WebInstallation.objects.get_or_create(pk=1)
    # Render no garantiza persistencia para SQLite sin disco persistente.
    # Bloqueamos por defecto el envío de dinero a bases efímeras.
    persistente = connection.vendor == 'postgresql'
    if request.method=='GET':
        return _respuesta({'schema':VERSION,'installation_id':str(web.instance_id),
                           'operations_receiver':True,'persistent_storage':persistente})
    if not persistente:
        return _respuesta({'error':'6E requiere PostgreSQL persistente en Render; no guardar ventas en SQLite efímero.'},503)
    try:
        largo=int(request.META.get('CONTENT_LENGTH') or '0')
        if largo>64*1024:return _respuesta({'error':'Evento demasiado grande.'},413)
        raw=request.body
        if len(raw)>64*1024:return _respuesta({'error':'Evento demasiado grande.'},413)
        p=json.loads(raw.decode('utf-8'))
        validar(p)
        if UUID(p['installation_id'])!=web.instance_id:
            return _respuesta({'error':'Identidad de restaurante diferente.'},409)
        event_id=UUID(p['event_id'])
        device_id=UUID(p['device_id'])
    except (ValueError,UnicodeError,TypeError,KeyError) as exc:
        return _respuesta({'error':str(exc)[:180]},400)
    # Idempotencia doble: UUID del evento y clave de negocio por terminal.
    # Los eventos NUNCA ejecutan una segunda venta en Pedido, ni afectan fiscal.
    with transaction.atomic():
        anterior=Desktop6eInbox.objects.select_for_update().filter(event_id=event_id).first()
        if anterior:
            if (anterior.digest!=p['digest'] or anterior.device_id!=device_id or
                anterior.installation_id!=web.instance_id or anterior.tipo!=p['tipo'] or anterior.origen!=p['origen']):
                return _respuesta({'error':'UUID reutilizado para otra operación.'},409)
            return _respuesta({'status':'ok','event_id':str(event_id),'duplicado':True})
        repetido=Desktop6eInbox.objects.filter(device_id=device_id,tipo=p['tipo'],origen=p['origen']).first()
        if repetido:
            return _respuesta({'error':'La operación ya existe con otro UUID. Revisar manualmente.'},409)
        try:
            with transaction.atomic():
                Desktop6eInbox.objects.create(
                    event_id=event_id,device_id=device_id,
                    installation_id=web.instance_id,tipo=p['tipo'],
                    origen=p['origen'],payload=p['payload'],
                    digest=p['digest'],token_label=credencial.label,
                )
        except IntegrityError:
            # Puede haber un envío concurrente; el siguiente reintento recibirá acuse.
            return _respuesta({'error':'Recepción concurrente; reintentá.'},503)
    return _respuesta({'status':'ok','event_id':str(event_id),'duplicado':False},201)
