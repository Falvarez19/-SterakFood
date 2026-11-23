"""Personalización opcional. No modifica ventas, precios, fiscales ni impresión."""
from __future__ import annotations

import io
import re
from PIL import Image, ImageOps, UnidentifiedImageError
from django.conf import settings
from django.contrib import messages
from django.db.utils import OperationalError, ProgrammingError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .context_processors import datos_marca, DEFAULTS
from .models import MarcaNegocio

HEX = re.compile(r'^#[0-9A-Fa-f]{6}$')
MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_IMAGE_SIDE = 1024


def autorizado(request):
    if getattr(settings, 'SM_LOCAL_MODE', False):
        try:
            from desktop_sm.permisos_local import permitido
            return permitido(request, 'propietario')
        except (ImportError, RuntimeError):
            return False
    # Web: una cuenta Django con privilegios de superusuario, no el PIN de caja.
    return bool(request.user.is_authenticated and request.user.is_superuser)


def _leer_png(fichero):
    if fichero.size > MAX_UPLOAD_BYTES:
        raise ValueError('La imagen supera 2 MB. Usá PNG, JPG o WebP más liviano.')
    if not fichero.size:
        raise ValueError('El archivo está vacío.')
    contenido = fichero.read(MAX_UPLOAD_BYTES + 1)
    try:
        with Image.open(io.BytesIO(contenido)) as img:
            if img.format not in ('PNG', 'JPEG', 'WEBP'):
                raise ValueError('Solo se aceptan imágenes PNG, JPG o WebP.')
            w, h = img.size
            if w > 4000 or h > 4000 or w * h > 5_000_000:
                raise ValueError('La imagen es demasiado grande. Usá una imagen de hasta 4000 píxeles y 5 megapíxeles.')
            img = ImageOps.exif_transpose(img)
            img.load()
            img = img.convert('RGBA')
            img.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE), Image.Resampling.LANCZOS)
            salida = io.BytesIO()
            img.save(salida, format='PNG', optimize=True)
            if salida.tell() > MAX_UPLOAD_BYTES:
                raise ValueError('La imagen resultante supera 2 MB.')
            return salida.getvalue()
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise ValueError('No se pudo leer la imagen. Probá otra imagen PNG, JPG o WebP.') from exc


@never_cache
@require_http_methods(['GET', 'POST'])
def configurar(request):
    if not autorizado(request):
        if getattr(settings, 'SM_LOCAL_MODE', False):
            return redirect('pedidos:login_dashboard')
        return redirect('marca:acceso')
    registro, _ = MarcaNegocio.objects.get_or_create(pk=1)
    if request.method == 'POST':
        try:
            nombre = (request.POST.get('nombre') or '').strip()
            nombre_corto = (request.POST.get('nombre_corto') or '').strip()
            subtitulo = (request.POST.get('subtitulo') or '').strip()
            if not (2 <= len(nombre) <= 90 and 2 <= len(nombre_corto) <= 45 and len(subtitulo) <= 160):
                raise ValueError('Revisá el nombre, el nombre corto y el subtítulo.')
            campos = {}
            for key in ('color_principal', 'color_secundario', 'color_acento'):
                color = (request.POST.get(key) or '').strip()
                if not HEX.fullmatch(color):
                    raise ValueError('Los colores deben tener formato #RRGGBB.')
                campos[key] = color.upper()
            logos = {}
            for key, field in (('logo_png', 'logo'), ('logo_claro_png', 'logo_claro')):
                archivo = request.FILES.get(field)
                if archivo:
                    logos[key] = _leer_png(archivo)
                elif request.POST.get(f'borrar_{field}') == '1':
                    logos[key] = None
            registro.nombre = nombre
            registro.nombre_corto = nombre_corto
            registro.subtitulo = subtitulo
            for key, value in {**campos, **logos}.items():
                setattr(registro, key, value)
            registro.colores_personalizados = any(
                campos[k].upper() != DEFAULTS[k].upper()
                for k in ('color_principal', 'color_secundario', 'color_acento')
            )
            registro.save()
            messages.success(request, 'Personalización guardada. Recargá el panel para ver los cambios.')
            return redirect('marca:configurar')
        except ValueError as exc:
            messages.error(request, str(exc))
    return render(request, 'marca/configurar.html', {'marca_actual': registro})


@never_cache
def tema_css(request):
    colores = datos_marca()
    prim, sec, ac = (colores[k] for k in ('color_principal','color_secundario','color_acento'))
    # Los únicos valores interpolados son hex validados por el formulario.
    for c in (prim, sec, ac):
        if not HEX.fullmatch(c):
            return HttpResponse('/* Tema inválido */', content_type='text/css', status=422)
    # Sin cambios explícitos: no introducir override que cambie la paleta SterakFood.
    if not colores['colores_personalizados']:
        contenido = '/* SterakFood: paleta original preservada. */\n'
    else:
        contenido = (
            ':root, body[data-theme="dark"], body[data-theme="light"] {'
            f'--naranja-sterak:{prim}; --naranja-brillo:{ac};'
            f'--azul-sanmartin:{prim}; --verde-sanmartin:{sec}; --dorado-sanmartin:{ac};'
            f'--marca-principal:{prim}; --marca-secundario:{sec}; --marca-acento:{ac};'
            '}\n'
        )
    response = HttpResponse(contenido, content_type='text/css; charset=utf-8')
    response['Cache-Control'] = 'no-store'
    return response


def _entregar_logo(campo, fallback):
    try:
        row = MarcaNegocio.objects.filter(pk=1).first()
    except (OperationalError, ProgrammingError):
        row = None
    contenido = getattr(row, campo, None) if row else None
    if not contenido and campo == 'logo_claro_png' and row:
        contenido = row.logo_png  # Logo principal para ambos temas si no hay segundo.
    if not contenido:
        return HttpResponseRedirect(static(fallback))
    response = HttpResponse(bytes(contenido), content_type='image/png')
    response['X-Content-Type-Options'] = 'nosniff'
    response['Cache-Control'] = 'private, no-store'
    return response


def logo(request):
    return _entregar_logo('logo_png', 'img/logo.png')


def logo_claro(request):
    return _entregar_logo('logo_claro_png', 'img/logo_2.png')


def manifiesto(request):
    """PWA por negocio: nombre e iconos sin tocar manifest.json a mano."""
    marca = datos_marca()
    response = JsonResponse({
        'name': marca['nombre'],
        'short_name': marca['nombre_corto'],
        'start_url': '/',
        'scope': '/',
        'display': 'standalone',
        'background_color': '#121212',
        'theme_color': marca['color_principal'],
        'icons': [
            {'src': reverse('marca:logo'), 'sizes': 'any', 'purpose': 'any'},
        ],
    })
    response['Cache-Control'] = 'no-store'
    return response


# STERAKFOOD_4B_ACCESO_PROPIETARIO_START
@never_cache
@require_http_methods(['GET', 'POST'])
def acceso(request):
    """Autenticación dentro de SterakFood, sin enviar al Django Admin.

    NO sustituir por el PIN del cajero: identidad visual y logos son ajustes
    de propietario. La sesión utiliza autenticación Django estándar + CSRF.
    """
    from django.contrib.auth import login as iniciar_sesion
    from django.contrib.auth.forms import AuthenticationForm

    if autorizado(request):
        return redirect('marca:configurar')
    if getattr(settings, 'SM_LOCAL_MODE', False):
        return redirect('pedidos:login_dashboard')
    form = AuthenticationForm(request=request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        usuario = form.get_user()
        if usuario.is_superuser and usuario.is_active:
            iniciar_sesion(request, usuario)
            return redirect('marca:configurar')
        form.add_error(None, 'Esta cuenta no tiene permiso para administrar la identidad del negocio.')
    return render(request, 'marca/acceso.html', {'form': form})
# STERAKFOOD_4B_ACCESO_PROPIETARIO_END

# STERAKFOOD_PASO_4E_ARCA_SOLO_PROPIETARIO
# Credenciales ARCA NUNCA se transmiten desde esta pagina ni se registran.
@never_cache
@require_http_methods(['GET', 'POST'])
def arca_propietario(request):
    """Administracion fiscal. No admite el PIN del cajero como autorizacion."""
    import os
    from django.contrib import messages as mensajes
    from pedidos.models import ConfiguracionFiscal

    if not autorizado(request):
        return redirect('marca:acceso')
    fiscal, _ = ConfiguracionFiscal.objects.get_or_create(pk=1)
    if request.method == 'POST':
        from pedidos.views import _cuit_valido
        razon = (request.POST.get('razon_social') or '').strip()
        cuit = (request.POST.get('cuit') or '').replace(' ', '').replace('-', '')
        condicion = (request.POST.get('condicion_iva') or '').strip()
        domicilio = (request.POST.get('domicilio_fiscal') or '').strip()
        pv_raw = (request.POST.get('punto_venta_referencia') or '').strip()
        if len(razon) > 180 or len(domicilio) > 220:
            mensajes.error(request, 'Los datos fiscales superan la longitud permitida.')
        elif cuit and not _cuit_valido(cuit):
            mensajes.error(request, 'El CUIT no es valido.')
        elif condicion not in dict(ConfiguracionFiscal.CONDICIONES_IVA):
            mensajes.error(request, 'Condicion impositiva no valida.')
        elif pv_raw and (not pv_raw.isascii() or not pv_raw.isdigit() or not 1 <= int(pv_raw) <= 99999):
            mensajes.error(request, 'El punto de venta debe estar entre 1 y 99999.')
        else:
            fiscal.razon_social = razon
            fiscal.cuit = cuit
            fiscal.condicion_iva = condicion
            fiscal.domicilio_fiscal = domicilio
            fiscal.punto_venta_referencia = int(pv_raw) if pv_raw else None
            fiscal.save()
            mensajes.success(request, 'Datos fiscales guardados. La emision sigue su configuracion independiente.')
            return redirect('marca:arca_propietario')
    # SOLO indicadores booleanos, nunca P12, contrasenas, token o clave privada.
    estado = {
        'entorno': os.environ.get('ARCA_ENV', 'homologacion'),
        'emision_habilitada': os.environ.get('ARCA_FISCAL_ENABLED') == '1',
        'certificado_configurado': bool(os.environ.get('ARCA_P12_BASE64', '').strip()),
        'punto_venta_configurado': bool(os.environ.get('ARCA_PUNTO_VENTA', '').strip()),
    }
    return render(request, 'marca/arca_propietario.html', {
        'fiscal': fiscal,
        'condiciones_iva': ConfiguracionFiscal.CONDICIONES_IVA,
        'estado': estado,
    })
