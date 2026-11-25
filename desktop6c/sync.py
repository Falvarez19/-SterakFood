"""Sincronización 6C: exclusivamente Web -> Desktop; NO sube ventas/cobros."""
from __future__ import annotations
import hashlib
import io
import re
from decimal import Decimal, InvalidOperation
from urllib.parse import quote

import requests
from PIL import Image, UnidentifiedImageError
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from marca.models import MarcaNegocio
from pedidos.models import Categoria, Producto, PuntoVenta, Configuracion
from .models import DesktopLink, DesktopSyncEvent, RemoteObjectMap
from .security import clean_server_url, decrypt_token, TOKEN_RE

MAX_JSON_BYTES = 10 * 1024 * 1024
MAX_IMAGE_BYTES = 3 * 1024 * 1024


def _request(url, key, maximum):
    if not TOKEN_RE.fullmatch(key):
        raise ValueError('Clave de vinculación incorrecta.')
    # Un token bearer solamente sale por HTTPS a una URL validada.
    with requests.get(url, headers={'Authorization': 'Bearer ' + key},
                      timeout=(6, 25), allow_redirects=False, stream=True) as response:
        if response.status_code != 200:
            raise ValueError(f'El servidor respondió HTTP {response.status_code}.')
        data = bytearray()
        for chunk in response.iter_content(chunk_size=65536):
            data.extend(chunk)
            if len(data) > maximum:
                raise ValueError('Respuesta remota demasiado grande.')
        return bytes(data)


def fetch_snapshot(server, key):
    import json
    server = clean_server_url(server)
    raw = _request(server + '/desktop/api/v1/catalogo/', key, MAX_JSON_BYTES)
    try:
        snapshot = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise ValueError('El servidor envió un catálogo inválido.') from exc
    if snapshot.get('schema') != 1:
        raise ValueError('La versión del catálogo remoto no es compatible.')
    if not (isinstance(snapshot.get('categorias'), list) and
            isinstance(snapshot.get('puestos'), list) and
            isinstance(snapshot.get('productos'), list)):
        raise ValueError('Faltan los datos del catálogo remoto.')
    if any(len(snapshot[k]) > n for k, n in [('categorias', 1500), ('puestos', 100), ('productos', 5000)]):
        raise ValueError('Catálogo demasiado grande para esta versión piloto.')
    return snapshot


def _unique(items, kind):
    seen = set()
    for item in items:
        if not isinstance(item, dict) or type(item.get('id')) is not int or item['id'] < 1 or item['id'] in seen:
            raise ValueError(f'Identificador {kind} duplicado o inválido.')
        seen.add(item['id'])
    return seen


def _safe_text(item, key, maximum, optional=False):
    value = item.get(key, '')
    if value is None and optional:
        return ''
    if not isinstance(value, str) or len(value) > maximum:
        raise ValueError('Campo del menú inválido: ' + key)
    return value


def _validate(snapshot):
    ids_category = _unique(snapshot['categorias'], 'categoría')
    ids_places = _unique(snapshot['puestos'], 'punto de venta')
    _unique(snapshot['productos'], 'producto')
    for item in snapshot['categorias']:
        _safe_text(item, 'nombre', 100)
    for item in snapshot['puestos']:
        for field, maximum in [('nombre', 50), ('slug', 50), ('telefono', 20)]:
            _safe_text(item, field, maximum)
        if type(item.get('abierto')) is not bool:
            raise ValueError('Estado inválido en punto de venta.')
    for item in snapshot['productos']:
        if item.get('categoria_id') not in ids_category or not isinstance(item.get('puestos'), list) or any(x not in ids_places for x in item['puestos']):
            raise ValueError('Producto con categoría o puesto inexistente.')
        for field, limit in [('nombre',200), ('codigo',20), ('descripcion',20000), ('foto_revision',500)]:
            _safe_text(item, field, limit)
        for field in ('variantes','guarniciones','puntos_coccion','rellenos','salsas','adicionales','opcion_hielo'):
            _safe_text(item, field, 255)
        try:
            precio = Decimal(str(item['precio']))
        except (ValueError, InvalidOperation, KeyError) as exc:
            raise ValueError('Precio remoto inválido.') from exc
        if not precio.is_finite() or precio < 0 or precio > Decimal('99999999.99') or precio.as_tuple().exponent < -2:
            raise ValueError('Precio fuera de rango.')
        if type(item.get('disponible')) is not bool or type(item.get('promocion')) is not bool:
            raise ValueError('Disponibilidad o promoción inválida.')
        if type(item.get('orden')) is not int or abs(item['orden']) > 1000000:
            raise ValueError('Orden de productos inválido.')
    from uuid import UUID
    try:
        UUID(str(snapshot['installation_id']))
    except (KeyError, ValueError) as exc:
        raise ValueError('Identidad web inválida.') from exc
    return True


def _fetch_image(link, token, kind, id=0, expected_hash=None):
    suffix = f'/{id}/' if id else '/'
    url = f'{link.server_url}/desktop/api/v1/archivo/{kind}{suffix}'
    raw = _request(url, token, MAX_IMAGE_BYTES)
    if expected_hash and hashlib.sha256(raw).hexdigest() != expected_hash:
        raise ValueError('La imagen cambió mientras se sincronizaba; reintentar.')
    try:
        with Image.open(io.BytesIO(raw)) as im:
            if im.format not in ('PNG','JPEG','WEBP','GIF') or im.width * im.height > 12_000_000:
                raise ValueError('Imagen no admitida.')
            im.verify()
    except (OSError, UnidentifiedImageError) as exc:
        raise ValueError('Imagen del catálogo inválida.') from exc
    return raw


def apply_snapshot(link, snapshot, token):
    """Valida antes de escribir. Nunca borra ventas, deudas ni productos históricos."""
    from uuid import UUID
    _validate(snapshot)
    if UUID(str(snapshot['installation_id'])) != link.web_instance_id:
        raise ValueError('El catálogo pertenece a otro restaurante. Se bloqueó la sincronización.')
    source_categories = {x['id']: x for x in snapshot['categorias']}
    source_places = {x['id']: x for x in snapshot['puestos']}
    source_products = {x['id']: x for x in snapshot['productos']}
    # Descarga de medios solo cuando cambian para no penalizar cada ciclo.
    old_maps = {(x.kind, x.remote_id): x for x in RemoteObjectMap.objects.all()}
    images = {}
    photo_warnings = 0
    for rid, item in source_products.items():
        rev = item['foto_revision']
        prev = old_maps.get(('producto', rid))
        if rev and (not prev or prev.photo_source != rev):
            try:
                images[rid] = _fetch_image(link, token, 'producto', rid)
            except (ValueError, requests.RequestException, OSError):
                # La falta de una foto nunca puede impedir actualizar precios.
                photo_warnings += 1
    binary_fields = ('logo_png','logo_claro_png','menu_fondo_archivo','menu_portada_archivo')
    brand_data = snapshot.get('marca') or {}
    brand_binary = brand_data.get('binarios') or {}
    current_brand = MarcaNegocio.objects.filter(pk=1).first()
    brand_files = {}
    for field in binary_fields:
        digest = brand_binary.get(field, '')
        if digest and (not current_brand or hashlib.sha256(bytes(getattr(current_brand, field) or b'')).hexdigest() != digest):
            try:
                brand_files[field] = _fetch_image(link, token, field, expected_hash=digest)
            except (ValueError, requests.RequestException, OSError):
                photo_warnings += 1
        elif not digest:
            brand_files[field] = None
    with transaction.atomic():
        category_ids, place_ids = {}, {}
        for rid, item in source_categories.items():
            mapping = old_maps.get(('categoria', rid))
            row = Categoria.objects.filter(pk=mapping.local_id).first() if mapping else None
            if not row:
                row = Categoria.objects.create(nombre=item['nombre'])
                RemoteObjectMap.objects.update_or_create(kind='categoria', remote_id=rid, defaults={'local_id':row.pk})
            elif row.nombre != item['nombre']:
                row.nombre = item['nombre']; row.save(update_fields=['nombre'])
            category_ids[rid] = row.pk
        for rid, item in source_places.items():
            mapping = old_maps.get(('puesto', rid))
            row = PuntoVenta.objects.filter(pk=mapping.local_id).first() if mapping else None
            slug = item['slug']
            if not row and PuntoVenta.objects.filter(slug=slug).exists():
                slug = f'web-{rid}'
            if not row:
                row = PuntoVenta.objects.create(nombre=item['nombre'], slug=slug,
                    telefono=item['telefono'], abierto=item['abierto'])
                RemoteObjectMap.objects.update_or_create(kind='puesto', remote_id=rid, defaults={'local_id': row.pk})
            else:
                row.nombre = item['nombre']; row.telefono = item['telefono']; row.abierto = item['abierto']
                row.save(update_fields=['nombre','telefono','abierto'])
            place_ids[rid] = row.pk
        for rid, item in source_products.items():
            mapping = old_maps.get(('producto', rid))
            row = Producto.objects.filter(pk=mapping.local_id).first() if mapping else None
            fields = {
                'categoria_id':category_ids[item['categoria_id']], 'nombre':item['nombre'],
                'codigo_rapido':item['codigo'] or None,'descripcion':item['descripcion'],
                'precio': Decimal(str(item['precio'])),'disponible':item['disponible'],
                'en_promocion':item['promocion'],'orden':item['orden'],
            }
            for name in ('variantes','guarniciones','puntos_coccion','rellenos','salsas','adicionales','opcion_hielo'):
                fields[name] = item[name]
            if not row:
                row = Producto.objects.create(**fields)
                mapping = RemoteObjectMap.objects.create(kind='producto', remote_id=rid, local_id=row.pk)
            else:
                for k, v in fields.items(): setattr(row, k, v)
                row.save(update_fields=list(fields.keys()))
            row.puntos_venta.set([place_ids[x] for x in item['puestos']])
            if rid in images:
                ext = 'png'
                with Image.open(io.BytesIO(images[rid])) as im:
                    ext = {'PNG':'png','WEBP':'webp','JPEG':'jpg','GIF':'gif'}[im.format]
                row.imagen.save(f'desktop6c_producto_{rid}.{ext}', ContentFile(images[rid]), save=True)
                mapping.photo_source = item['foto_revision']
                mapping.save(update_fields=['photo_source'])
            elif not item['foto_revision'] and row.imagen:
                # Quitar imagen de catálogo, pero NO borrar archivo de ventas antiguas.
                row.imagen = None
                row.save(update_fields=['imagen'])
                if mapping:
                    mapping.photo_source = ''
                    mapping.save(update_fields=['photo_source'])
        for rid, mapping in [((obj.kind, obj.remote_id),obj) for obj in old_maps.values()]:
            if rid[0] == 'producto' and rid[1] not in source_products:
                Producto.objects.filter(pk=mapping.local_id).update(disponible=False)
            if rid[0] == 'puesto' and rid[1] not in source_places:
                PuntoVenta.objects.filter(pk=mapping.local_id).update(abierto=False)
        visual_fields = (
            'nombre','nombre_corto','subtitulo','color_principal','color_secundario',
            'color_acento','colores_personalizados','menu_fuente','menu_titulo_px',
            'menu_producto_px','menu_descripcion_px','menu_precio_px','menu_color_fondo',
            'menu_color_boton','menu_portada_mime','menu_mostrar_portada',
            'menu_oscurecer','menu_tarjetas_iguales','menu_sombra_tarjetas',
            'menu_borde_px','menu_boton_estilo')
        if brand_data:
            brand, _ = MarcaNegocio.objects.get_or_create(pk=1)
            for field in visual_fields:
                if field in brand_data:
                    setattr(brand, field, brand_data[field])
            for field, raw in brand_files.items():
                setattr(brand, field, raw)
            brand.save()
        config, _ = Configuracion.objects.get_or_create(pk=1)
        try:
            mesas = int(snapshot.get('mesas_visibles', config.numero_mesas_visibles))
            config.numero_mesas_visibles = max(1, min(100, mesas))
            config.salon_habilitado = bool(snapshot.get('salon_habilitado', True))
            config.save(update_fields=['numero_mesas_visibles','salon_habilitado'])
        except (ValueError, TypeError):
            pass
        summary = ('Catálogo y marca actualizados' if photo_warnings == 0 else
                   f'Precios actualizados; {photo_warnings} imagen(es) sin descargar')
        link.last_sync_at = timezone.now(); link.last_error = ('' if photo_warnings == 0 else summary)
        link.save(update_fields=['last_sync_at','last_error'])
        DesktopSyncEvent.objects.create(ok=True, summary=summary, products_count=len(source_products))
    return len(source_products)


def run_sync():
    """Falla de red: deja última copia intacta y guarda un informe local."""
    if not getattr(settings, 'STERAK_DESKTOP_MODE', False):
        raise RuntimeError('Nunca sincronizar desde el servidor web.')
    link = DesktopLink.objects.first()
    if link is None:
        return False
    try:
        from .locking import sync_lock
        with sync_lock(settings.DATA_DIR) as acquired:
            if not acquired:
                return False
            key = decrypt_token(link.token_ciphertext)
            snapshot = fetch_snapshot(link.server_url, key)
            apply_snapshot(link, snapshot, key)
            return True
    except Exception as exc:
        message = str(exc)[:480]
        link.last_error = message
        link.save(update_fields=['last_error'])
        DesktopSyncEvent.objects.create(ok=False, summary=message[:350])
        return False
