"""SterakFood 6A: personalización visual por instalación.

No guarda medios en MEDIA_ROOT para evitar pérdidas en Render.
No modifica POS ni la configuración fiscal.
"""
from __future__ import annotations
import io
import re
from django.db.utils import OperationalError, ProgrammingError
from django.http import HttpResponse, HttpResponseRedirect
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from PIL import Image, ImageOps, UnidentifiedImageError

FONT_STACKS = {
    'original': None,
    'moderna': '"Trebuchet MS", "Segoe UI", Arial, sans-serif',
    'clasica': 'Georgia, "Times New Roman", serif',
    'elegante': '"Palatino Linotype", "Book Antiqua", Georgia, serif',
    'cursiva': '"Segoe Script", "Brush Script MT", cursive',
    'suave': '"Segoe UI", "Century Gothic", sans-serif',
}
HEX6 = re.compile(r'^#[0-9a-fA-F]{6}$')
MIME_TYPES = {'GIF': 'image/gif', 'PNG': 'image/png', 'JPEG': 'image/jpeg', 'WEBP': 'image/webp'}


def _int_choice(request, name, current, low, high):
    value = request.POST.get(name)
    if value is None:
        return current
    try:
        n = int(value)
    except (TypeError, ValueError):
        raise ValueError('Revisá el valor de ' + name.replace('menu_', '').replace('_', ' ') + '.')
    if not low <= n <= high:
        raise ValueError('El tamaño o ajuste de ' + name.replace('menu_', '').replace('_', ' ') + ' está fuera de rango.')
    return n


def _image_upload(file, *, animated=False):
    """Valida la imagen real, no la extensión ni el tipo HTTP recibido."""
    if not file:
        return None
    maximum = 3 * 1024 * 1024 if animated else 5 * 1024 * 1024
    if not 0 < file.size <= maximum:
        raise ValueError('La imagen supera el límite permitido (GIF 3 MB; fondo 5 MB).')
    raw = file.read(maximum + 1)
    if len(raw) > maximum:
        raise ValueError('El archivo excede el tamaño permitido.')
    try:
        with Image.open(io.BytesIO(raw)) as im:
            fmt = im.format
            if fmt not in MIME_TYPES:
                raise ValueError('Usá PNG, JPG, WebP o GIF.')
            w, h = im.size
            if w > 5000 or h > 5000 or w * h > 10_000_000:
                raise ValueError('La imagen es demasiado grande (máximo 10 megapíxeles).')
            frames = getattr(im, 'n_frames', 1)
            if animated and frames > 80:
                raise ValueError('El GIF supera el límite de 80 cuadros.')
            if not animated and frames > 1:
                raise ValueError('El fondo debe ser una imagen fija (PNG, JPG o WebP).')
            if animated and fmt == 'GIF':
                # La animación se conserva: se inspeccionan los cuadros antes de guardar.
                if w * h * frames > 90_000_000:
                    raise ValueError('El GIF es demasiado pesado para el menú.')
                for i in range(frames):
                    im.seek(i)
                    im.load()
                return raw, 'image/gif'
            im.seek(0)
            im.load()
            im = ImageOps.exif_transpose(im)
            im.thumbnail((2000 if not animated else 1600, 2000 if not animated else 1600), Image.Resampling.LANCZOS)
            if im.mode not in ('RGB', 'RGBA'):
                im = im.convert('RGBA' if 'A' in im.getbands() else 'RGB')
            out = io.BytesIO()
            im.save(out, format='WEBP', quality=84, method=5)
            if out.tell() > 3 * 1024 * 1024:
                raise ValueError('La imagen comprimida sigue siendo demasiado pesada.')
            return out.getvalue(), 'image/webp'
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise ValueError('No se pudo leer la imagen. Verificá el archivo.') from exc


def cambios_visuales(request, registro):
    """Devuelve cambios validados; la vista los guarda junto a la identidad existente."""
    changes = {}
    nombre = request.POST.get('menu_fuente')
    if nombre is not None:
        if nombre not in FONT_STACKS:
            raise ValueError('Elegí una fuente válida.')
        changes['menu_fuente'] = nombre
    for key, low, high in (
        ('menu_titulo_px', 20, 62), ('menu_producto_px', 12, 30),
        ('menu_descripcion_px', 11, 24), ('menu_precio_px', 12, 36),
        ('menu_borde_px', 0, 30), ('menu_oscurecer', 0, 85),
    ):
        changes[key] = _int_choice(request, key, getattr(registro, key), low, high)
    for key in ('menu_color_fondo', 'menu_color_boton'):
        value = request.POST.get(key)
        if value is not None:
            if not HEX6.fullmatch(value):
                raise ValueError('El color del menú debe tener formato #RRGGBB.')
            changes[key] = value.upper()
    if 'menu_ajustes_6a' in request.POST:
        for key in ('menu_tarjetas_iguales', 'menu_sombra_tarjetas', 'menu_mostrar_portada'):
            changes[key] = request.POST.get(key) == 'on'
    estilo = request.POST.get('menu_boton_estilo')
    if estilo is not None:
        if estilo not in ('normal', 'redondo', 'recto'):
            raise ValueError('Estilo de botón inválido.')
        changes['menu_boton_estilo'] = estilo

    for field, key, kind in (
        ('archivo_fondo_menu', 'menu_fondo_archivo', False),
        ('archivo_portada_menu', 'menu_portada_archivo', True),
    ):
        archivo = request.FILES.get(field)
        if archivo:
            body, mime = _image_upload(archivo, animated=kind)
            changes[key] = body
            if kind:
                changes['menu_portada_mime'] = mime
        elif request.POST.get('borrar_' + field) == '1':
            changes[key] = None
            if kind:
                changes['menu_portada_mime'] = ''
    return changes


def _registro():
    from .models import MarcaNegocio
    try:
        return MarcaNegocio.objects.filter(pk=1).first()
    except (OperationalError, ProgrammingError):
        return None


def _respuesta_imagen(contenido, mime):
    response = HttpResponse(bytes(contenido), content_type=mime)
    response['X-Content-Type-Options'] = 'nosniff'
    response['Cache-Control'] = 'public, max-age=300'
    return response


@never_cache
@require_GET
def menu_fondo(request):
    row = _registro()
    if row and row.menu_fondo_archivo:
        return _respuesta_imagen(row.menu_fondo_archivo, 'image/webp')
    return HttpResponse(status=404)


@never_cache
@require_GET
def menu_portada(request):
    row = _registro()
    if row and row.menu_portada_archivo and row.menu_mostrar_portada:
        mime = row.menu_portada_mime if row.menu_portada_mime in ('image/webp', 'image/gif') else 'image/webp'
        return _respuesta_imagen(row.menu_portada_archivo, mime)
    return HttpResponseRedirect(static('img/fondo-buffet.png'))


@never_cache
@require_GET
def menu_tema_css(request):
    row = _registro()
    if not row:
        return HttpResponse('/* Sin ajustes de menú 6A. */', content_type='text/css; charset=utf-8')
    font = FONT_STACKS.get(row.menu_fuente)
    styles = ['/* SterakFood 6A — configuración visual del menú público */']
    scope = '.menu-principal-moderno'
    if font:
        styles.append(f'{scope}, .hero-menu-moderno {{ font-family:{font} !important; }}')
        styles.append(f'{scope} button, {scope} input, {scope} select {{ font-family:{font} !important; }}')
    sizes = (
        ('.hero-menu-moderno h1, .menu-principal-moderno .seccion-titulo, .menu-principal-moderno .categoria-encabezado h2', row.menu_titulo_px),
        (f'{scope} .tarjeta-cuerpo h3, {scope} .tarjeta-producto h3', row.menu_producto_px),
        (f'{scope} .tarjeta-producto .descripcion', row.menu_descripcion_px),
        (f'{scope} .tarjeta-producto .precio', row.menu_precio_px),
    )
    for selector, px in sizes:
        styles.append(f'{selector} {{ font-size:{int(px)}px !important; }}')
    if not row.menu_fondo_archivo and HEX6.fullmatch(row.menu_color_fondo) and row.menu_color_fondo.upper() != '#121212':
        styles.append(f'body {{ background-color:{row.menu_color_fondo} !important; background-image:none !important; }}')
    if row.menu_fondo_archivo:
        opacity = min(85, max(0, int(row.menu_oscurecer))) / 100
        fondo_url = reverse('marca:menu_fondo_6a')
        # Solo se carga este CSS en inicio.html: no modifica el POS ni el panel.
        styles.append(
            'body { '
            f'background-image:linear-gradient(rgba(0,0,0,{opacity:.2f}),rgba(0,0,0,{opacity:.2f})),url("{fondo_url}") !important; '
            f'background-color:{row.menu_color_fondo if HEX6.fullmatch(row.menu_color_fondo) else "#121212"} !important; '
            'background-position:center top !important; background-repeat:no-repeat !important; '
            'background-size:cover !important; background-attachment:fixed !important; }'
        )
        styles.append('.menu-principal-moderno { background:transparent !important; }')
    if HEX6.fullmatch(row.menu_color_boton):
        styles.append(f'{scope} .btn-agregar {{ background-color:{row.menu_color_boton} !important; }}')
    radius = min(30, max(0, int(row.menu_borde_px)))
    styles.append(f'{scope} .tarjeta-producto {{ border-radius:{radius}px !important; overflow:hidden; }}')
    shadow = '0 8px 25px rgba(0,0,0,.22)' if row.menu_sombra_tarjetas else 'none'
    styles.append(f'{scope} .tarjeta-producto {{ box-shadow:{shadow} !important; }}')
    btn_radius = ('999px' if row.menu_boton_estilo == 'redondo' else '3px' if row.menu_boton_estilo == 'recto' else f'{radius}px')
    styles.append(f'{scope} .btn-agregar {{ border-radius:{btn_radius} !important; }}')
    if row.menu_tarjetas_iguales:
        styles.append(f'''
{scope} .menu-horizontal > .tarjeta-producto,
{scope} .productos-grid > .tarjeta-producto,
{scope} .menu-grid > .tarjeta-producto,
{scope} .grid-productos > .tarjeta-producto {{
    display:flex !important; flex-direction:column !important; height:auto !important;
    align-self:stretch; min-height:100%;
}}
{scope} .menu-grid {{ align-items:stretch; }}
{scope} .tarjeta-producto .tarjeta-imagen {{ width:100%; flex-shrink:0; overflow:hidden; }}
{scope} .tarjeta-producto .tarjeta-imagen img {{ width:100%; height:180px; object-fit:cover; display:block; }}
{scope} .tarjeta-producto .tarjeta-cuerpo {{ flex:1 0 auto; display:flex; flex-direction:column; }}
{scope} .tarjeta-producto .tarjeta-cuerpo h3 {{ line-height:1.3; min-height:2.6em; display:-webkit-box; -webkit-box-orient:vertical; -webkit-line-clamp:2; overflow:hidden; }}
{scope} .tarjeta-producto .descripcion {{ line-height:1.4; min-height:4.2em; display:-webkit-box; -webkit-box-orient:vertical; -webkit-line-clamp:3; overflow:hidden; }}
{scope} .tarjeta-producto .tarjeta-pie {{ margin-top:auto !important; display:flex; flex-direction:column; justify-content:flex-end; gap:9px; width:100%; }}
{scope} .tarjeta-producto .btn-agregar {{ width:100%; min-height:38px; }}
@media(max-width:600px) {{ {scope} .tarjeta-producto .tarjeta-imagen img {{ height:155px; }} }}
''')
    # Compatibilidad visual: aplica el tema aunque el menú no use las clases antiguas.
    # El JS añade sf6a-menu solamente en la portada del menú público.
    generic = '.sf6a-menu .producto-card, .sf6a-menu .card-producto, .sf6a-menu .menu-card, .sf6a-menu .producto-tarjeta'
    if font:
        styles.append(f'body.sf6a-menu main, body.sf6a-menu main button {{ font-family:{font} !important; }}')
    styles.extend([
        f'body.sf6a-menu main h2 {{ font-size:{int(row.menu_titulo_px)}px !important; }}',
        f'body.sf6a-menu main .producto-card h3, body.sf6a-menu main .card-producto h3, body.sf6a-menu main .menu-card h3 {{ font-size:{int(row.menu_producto_px)}px !important; }}',
        f'body.sf6a-menu main .producto-card .descripcion, body.sf6a-menu main .card-producto .descripcion {{ font-size:{int(row.menu_descripcion_px)}px !important; }}',
        f'body.sf6a-menu main .producto-card .precio, body.sf6a-menu main .card-producto .precio {{ font-size:{int(row.menu_precio_px)}px !important; }}',
        f'{generic} {{ border-radius:{radius}px !important; box-shadow:{shadow} !important; overflow:hidden; }}',
    ])
    if HEX6.fullmatch(row.menu_color_boton):
        styles.append(f'body.sf6a-menu main .btn-agregar, body.sf6a-menu main .agregar-producto {{ background-color:{row.menu_color_boton} !important; border-radius:{btn_radius} !important; }}')
    if row.menu_tarjetas_iguales:
        styles.append('''
.sf6a-menu .productos-grid > .producto-card, .sf6a-menu .productos-grid > .card-producto,
.sf6a-menu .menu-grid > .producto-card, .sf6a-menu .menu-grid > .card-producto {
  display:flex !important;flex-direction:column !important;align-self:stretch;height:100%;
}
.sf6a-menu .producto-card img, .sf6a-menu .card-producto img {object-fit:cover;}
.sf6a-menu .producto-card .btn-agregar, .sf6a-menu .card-producto .btn-agregar {margin-top:auto;}
''')
    response = HttpResponse('\n'.join(styles), content_type='text/css; charset=utf-8')
    response['Cache-Control'] = 'no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    return response
