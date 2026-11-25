"""API de SOLO LECTURA: web -> Desktop. Requiere token por instalación."""
import hashlib
import json
import mimetypes
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from marca.models import MarcaNegocio
from pedidos.models import Producto, Categoria, PuntoVenta, Configuracion
from .models import DesktopAccessToken, WebInstallation
from .security import TOKEN_RE, token_hash


def _authenticate(request):
    if getattr(settings, 'STERAK_DESKTOP_MODE', False):
        return None
    value = request.headers.get('Authorization', '')
    if not value.startswith('Bearer '):
        return None
    raw = value[7:]
    if not TOKEN_RE.fullmatch(raw):
        return None
    row = DesktopAccessToken.objects.filter(token_hash=token_hash(raw), active=True).first()
    if row:
        DesktopAccessToken.objects.filter(pk=row.pk).update(last_used_at=timezone.now())
    return row


def _denied():
    response = JsonResponse({'error': 'Sin autorización.'}, status=401)
    response['WWW-Authenticate'] = 'Bearer'
    response['Cache-Control'] = 'no-store'
    return response


@never_cache
@require_GET
def catalog(request):
    if not _authenticate(request):
        return _denied()
    web, _ = WebInstallation.objects.get_or_create(pk=1)
    items = []
    for p in Producto.objects.select_related('categoria').prefetch_related('puntos_venta').all():
        media = ''
        if p.imagen and p.imagen.name:
            try:
                media = p.imagen.name + ':' + str(p.imagen.size)
            except (OSError, ValueError):
                media = p.imagen.name
        items.append({
            'id': p.pk, 'categoria_id': p.categoria_id,
            'puestos': [x.pk for x in p.puntos_venta.all()],
            'nombre': p.nombre, 'codigo': p.codigo_rapido or '',
            'descripcion': p.descripcion or '', 'precio': str(p.precio),
            'disponible': p.disponible, 'promocion': p.en_promocion,
            'orden': p.orden, 'foto_revision': media,
            **{k: (getattr(p, k) or '') for k in (
                'variantes','guarniciones','puntos_coccion','rellenos','salsas',
                'adicionales','opcion_hielo')},
        })
    brand = MarcaNegocio.objects.filter(pk=1).first()
    visual_fields = (
        'nombre','nombre_corto','subtitulo','color_principal','color_secundario',
        'color_acento','colores_personalizados','menu_fuente','menu_titulo_px',
        'menu_producto_px','menu_descripcion_px','menu_precio_px',
        'menu_color_fondo','menu_color_boton','menu_portada_mime',
        'menu_mostrar_portada','menu_oscurecer','menu_tarjetas_iguales',
        'menu_sombra_tarjetas','menu_borde_px','menu_boton_estilo',
    )
    binary_fields = ('logo_png','logo_claro_png','menu_fondo_archivo','menu_portada_archivo')
    brand_data = {f: getattr(brand, f) for f in visual_fields} if brand else {}
    brand_data['binarios'] = {f: hashlib.sha256(bytes(getattr(brand, f) or b'')).hexdigest() if brand and getattr(brand, f) else '' for f in binary_fields}
    config = Configuracion.objects.filter(pk=1).first()
    response = JsonResponse({
        'schema': 1, 'installation_id': str(web.instance_id),
        'marca': brand_data,
        'mesas_visibles': config.numero_mesas_visibles if config else 100,
        'salon_habilitado': config.salon_habilitado if config else True,
        'puestos': list(PuntoVenta.objects.all().values('id','nombre','slug','telefono','abierto')),
        'categorias': list(Categoria.objects.all().values('id','nombre')),
        'productos': items,
    }, json_dumps_params={'ensure_ascii': False})
    response['Cache-Control'] = 'no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    return response


@never_cache
@require_GET
def asset(request, kind, remote_id=0):
    if not _authenticate(request):
        return _denied()
    if kind == 'producto':
        p = Producto.objects.filter(pk=remote_id).first()
        if not p or not p.imagen:
            return HttpResponse(status=404)
        try:
            with p.imagen.open('rb') as f:
                data = f.read(3 * 1024 * 1024 + 1)
        except (OSError, ValueError):
            return HttpResponse(status=404)
        if len(data) > 3 * 1024 * 1024:
            return HttpResponse(status=413)
        mime = mimetypes.guess_type(p.imagen.name)[0] or 'application/octet-stream'
    else:
        if kind not in ('logo_png','logo_claro_png','menu_fondo_archivo','menu_portada_archivo'):
            return HttpResponse(status=404)
        row = MarcaNegocio.objects.filter(pk=1).first()
        data = bytes(getattr(row, kind) or b'') if row else b''
        if not data:
            return HttpResponse(status=404)
        mime = 'image/gif' if kind == 'menu_portada_archivo' and row.menu_portada_mime == 'image/gif' else ('image/png' if kind.startswith('logo') else 'image/webp')
    response = HttpResponse(data, content_type=mime)
    response['Cache-Control'] = 'no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    return response
