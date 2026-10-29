import secrets
import hashlib
import logging
import uuid
import unicodedata
# SISTEMA SM: vistas, carrito, dashboard, impresión y APIs
from decimal import Decimal, InvalidOperation
from datetime import datetime
import json
import re
import requests
import urllib.parse
import mercadopago
import os
import tarfile
from django.db import connection, transaction
from django.db.models import Q, Sum
from django.conf import settings
from django.core.management import call_command
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.http import JsonResponse, HttpResponse, Http404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.utils.timezone import localtime
from django.utils import timezone
from django.core.cache import cache
from .forms import ProductoForm
from .models import (Producto, Pedido, DetallePedido, PuntoVenta, Categoria, Configuracion, OpinionCliente, Mozo, CuentaCorriente, MovimientoCuentaCorriente, ComprobanteCuentaCorriente, ImpresionComprobanteCuenta)
from django.core.exceptions import PermissionDenied
from django.contrib.staticfiles import finders
from .models import CorteHistorialVentas, BorradorFiscal, ConfiguracionFiscal, OperacionCobroSalon
from uuid import UUID
from django.db import IntegrityError

# ==========================================================================
# CONFIGURACIÓN GLOBAL DEL SISTEMA
# ==========================================================================

def obtener_configuracion():
    config, _ = Configuracion.objects.get_or_create(id=1)
    return config


def descuento_efectivo_vigente(config):
    return bool(getattr(config, 'descuento_efectivo_activo', False))


def cierre_automatico_en_curso(config):
    """Compatibilidad con plantillas anteriores. v136 opera SOLO manualmente.

    Incluso si la base antigua tiene 'cierre_automatico_activo=True',
    nunca se cambian pedidos por reloj, navegador cerrado ni desconexion.
    """
    return False




def pedidos_online_habilitados(config):
    """Leer unicamente el interruptor explicitamente configurado en Render."""
    return bool(config.buffet_habilitado)




POPUP_BIENVENIDA_MAX = 3
POPUP_BIENVENIDA_EXTS = ['webp', 'png', 'jpg', 'jpeg']


def carpeta_popup_bienvenida():
    carpeta_popup = os.path.join(settings.MEDIA_ROOT, 'popup')
    os.makedirs(carpeta_popup, exist_ok=True)
    return carpeta_popup


def obtener_popup_bienvenida_archivos():
    carpeta_popup = carpeta_popup_bienvenida()
    archivos = []

    for nombre in os.listdir(carpeta_popup):
        nombre_lower = nombre.lower()

        # Soporta la imagen vieja bienvenida_popup.ext
        # y las nuevas bienvenida_popup_1.ext / _2 / _3.
        if not nombre_lower.startswith('bienvenida_popup'):
            continue

        extension = os.path.splitext(nombre_lower)[1].replace('.', '')
        if extension not in POPUP_BIENVENIDA_EXTS:
            continue

        ruta = os.path.join(carpeta_popup, nombre)
        if os.path.isfile(ruta):
            archivos.append(ruta)

    def ordenar_popup(ruta):
        nombre = os.path.basename(ruta).lower()
        match = re.search(r'bienvenida_popup_(\d+)', nombre)
        if match:
            return int(match.group(1))
        return 1

    return sorted(archivos, key=ordenar_popup)[:POPUP_BIENVENIDA_MAX]


def obtener_popup_bienvenida_archivo():
    archivos = obtener_popup_bienvenida_archivos()

    if archivos:
        return archivos[0]

    ruta_static = finders.find('img/bienvenida_buffet.webp')
    if ruta_static:
        return ruta_static

    return None


def bienvenida_disponible():
    return bool(obtener_popup_bienvenida_archivo())


def bienvenida_popup_urls():
    urls = []

    for ruta in obtener_popup_bienvenida_archivos():
        nombre_archivo = os.path.basename(ruta)
        version = int(os.path.getmtime(ruta))
        urls.append({
            'nombre': nombre_archivo,
            'url': f"{settings.MEDIA_URL}popup/{nombre_archivo}?v={version}",
        })

    # Fallback viejo del static, solo cuando no hay imágenes subidas.
    if not urls:
        ruta_static = finders.find('img/bienvenida_buffet.webp')
        if ruta_static:
            urls.append({
                'nombre': 'bienvenida_buffet.webp',
                'url': f"{settings.STATIC_URL}img/bienvenida_buffet.webp",
            })

    return urls


def bienvenida_popup_url():
    urls = bienvenida_popup_urls()
    return urls[0]['url'] if urls else ''


def limpiar_popup_bienvenida_media(nombre_archivo=None):
    carpeta_popup = carpeta_popup_bienvenida()

    if nombre_archivo:
        nombre_seguro = os.path.basename(nombre_archivo)

        if not nombre_seguro.lower().startswith('bienvenida_popup'):
            return

        ruta = os.path.join(carpeta_popup, nombre_seguro)

        if os.path.exists(ruta):
            os.remove(ruta)

        return

    for ruta in obtener_popup_bienvenida_archivos():
        if os.path.exists(ruta):
            os.remove(ruta)


# ==========================================================================
# MÓDULO 1: VISTAS DEL CLIENTE (MENÚ PÚBLICO)
# ==========================================================================

@never_cache
def bienvenida(request):
    config = obtener_configuracion()
    buffet_habilitado = pedidos_online_habilitados(config)
    puestos = PuntoVenta.objects.filter(abierto=True)
    return render(request, 'pedidos/bienvenida.html', {
        'puestos': puestos,
        'buffet_habilitado': buffet_habilitado
    })
@never_cache
def inicio(request):
    config = obtener_configuracion()
    buffet_habilitado = pedidos_online_habilitados(config)
    descuento_activo = descuento_efectivo_vigente(config)
    # ==========================================================
    # MOSTRADOR ACTUAL
    # ==========================================================
    puesto_slug = (
        request.GET.get('puesto')
        or
        request.session.get('puesto_carrito')
    )
    if puesto_slug:
        puesto_activo = (
            PuntoVenta.objects
            .filter(
                slug=puesto_slug
            )
            .first()
        )
    else:
        puesto_activo = (
            PuntoVenta.objects
            .first()
        )
    # ==========================================================
    # PRODUCTOS DEL MOSTRADOR
    # ==========================================================
    if puesto_activo:
        productos = (
            Producto.objects
            .filter(
                disponible=True,
                puntos_venta=puesto_activo
            )
            .exclude(
                categoria__nombre='Salon'
            )
            .select_related(
                'categoria'
            )
            .order_by(
                'categoria__nombre',
                'orden',
                'nombre'
            )
        )
        if (
            request.session.get(
                'puesto_carrito'
            )
            !=
            puesto_activo.slug
        ):
            request.session[
                'carrito'
            ] = {}
            request.session[
                'puesto_carrito'
            ] = puesto_activo.slug
            request.session.modified = True
    else:
        productos = (
            Producto.objects
            .filter(
                disponible=True
            )
            .exclude(
                categoria__nombre='Salon'
            )
            .select_related(
                'categoria'
            )
            .order_by(
                'categoria__nombre',
                'orden',
                'nombre'
            )
        )
    # ==========================================================
    # PROMOCIONES
    # ==========================================================
    #
    # Solo aparecen productos que:
    #
    # - Vos marcaste como PROMO desde el Dashboard.
    # - Están disponibles.
    # - Pertenecen al mostrador que está viendo el cliente.
    #
    # ==========================================================
    promociones = (
        productos.filter(en_promocion=True).order_by('orden', 'nombre')
        if getattr(config, 'mostrar_promociones', True)
        else Producto.objects.none()
    )
    # ==========================================================
    # RENDER
    # ==========================================================
    return render(
        request,
        'pedidos/inicio.html',
        {
            'puesto_activo':
                puesto_activo,
            'productos':
                productos,
            'promociones':
                promociones,
            'buffet_habilitado':
                buffet_habilitado,
            'descuento_activo':
                descuento_activo,
            'mozos':
                Mozo.objects.all().order_by('nombre'),
            'descuento_porcentaje': getattr(config, 'descuento_efectivo_porcentaje', 10),
            'mostrar_promociones': getattr(config, 'mostrar_promociones', True),
            'mostrar_opiniones': getattr(config, 'mostrar_opiniones', True),
            'mostrar_google_reviews': getattr(config, 'mostrar_google_reviews', True),
            'welcome_modal_enabled': getattr(config, 'mostrar_bienvenida', False) and bienvenida_disponible(),
            'bienvenida_popup_url': bienvenida_popup_url(),
            'bienvenida_popup_urls': bienvenida_popup_urls(),
            'salon_habilitado': getattr(config, 'salon_habilitado', True),
            'cierre_automatico_en_curso': cierre_automatico_en_curso(config),
            'google_review_url': getattr(settings, 'GOOGLE_REVIEW_URL', ''),
        }
    )
# ==========================================================================
# MÓDULO 2: LÓGICA INTERNA DEL CARRITO DE COMPRAS (SESIONES)
# ==========================================================================

def obtener_carrito_seguro(request):
    carrito = request.session.get('carrito', {})
    if any(not isinstance(data, dict) for data in carrito.values()):
        carrito = {}
        request.session['carrito'] = carrito
        request.session.modified = True
    return carrito
def agregar_al_carrito(request, producto_id):
    config = Configuracion.objects.first()
    if config and not config.buffet_habilitado:
        return JsonResponse({'status': 'error', 'mensaje': 'Los pedidos están desactivados temporalmente.'})
    producto = get_object_or_404(Producto, id=producto_id)
    variante = request.GET.get('variante', '')
    guarnicion = request.GET.get('guarnicion', '')
    punto = request.GET.get('punto', '')
    relleno = request.GET.get('relleno', '')
    salsa = request.GET.get('salsa', '')
    adicional = request.GET.get('adicional', '')
    hielo = request.GET.get('hielo', '')
    puesto_actual = request.GET.get('puesto')
    carrito = obtener_carrito_seguro(request)
    puestos_producto = producto.puntos_venta.values_list('slug', flat=True)
    if puesto_actual and puesto_actual not in puestos_producto:
        carrito = {}
    llave_str = str(producto_id)
    if variante: llave_str += f"_{variante}"
    if guarnicion: llave_str += f"_{guarnicion}"
    if punto: llave_str += f"_{punto}"
    if relleno: llave_str += f"_{relleno}"
    if salsa: llave_str += f"_{salsa}"
    if adicional: llave_str += f"_{adicional}"
    if hielo: llave_str += f"_{hielo}"
    if llave_str in carrito:
        carrito[llave_str]['cantidad'] += 1
    else:
        carrito[llave_str] = {
            'producto_id': producto_id,
            'cantidad': 1,
            'variante': variante,
            'guarnicion': guarnicion,
            'punto': punto,
            'relleno': relleno,
            'salsa': salsa,
            'adicional': adicional,
            'hielo': hielo,
        }
    request.session['carrito'] = carrito
    request.session.modified = True
    total_items = sum(item['cantidad'] for item in carrito.values())
    return JsonResponse({'status': 'ok', 'total_items': total_items})
def ver_carrito(request):
    carrito = obtener_carrito_seguro(request)
    items = []
    total_general = 0
    for llave, data in carrito.items():
        try:
            prod = Producto.objects.get(id=int(data['producto_id']))
            precio_base = float(prod.precio)
            total_extras = 0
            opciones_elegidas = ['variante', 'guarnicion', 'punto', 'relleno', 'salsa', 'adicional', 'hielo']
            for clave in opciones_elegidas:
                texto_opcion = data.get(clave, '')
                if texto_opcion:
                    if "(+" in texto_opcion:
                        precios_pos = re.findall(r'\(\+(\d+(?:\.\d+)?)\)', texto_opcion)
                        for p in precios_pos:
                            total_extras += float(p)
                    if "(-" in texto_opcion:
                        precios_neg = re.findall(r'\(\-(\d+(?:\.\d+)?)\)', texto_opcion)
                        for n in precios_neg:
                            total_extras -= float(n)
            precio_final = precio_base + total_extras
            sub = precio_final * data['cantidad']
            total_general += sub
            nombre_completo = prod.nombre
            opciones = []
            if data.get('variante'): opciones.append(data['variante'])
            if data.get('guarnicion'): opciones.append(data['guarnicion'])
            if data.get('punto'): opciones.append(f"Punto: {data['punto']}")
            if data.get('relleno'): opciones.append(f"Relleno: {data['relleno']}")
            if data.get('salsa'): opciones.append(f"Salsa: {data['salsa']}")
            if data.get('adicional'): opciones.append(f"Extra: {data['adicional']}")
            if data.get('hielo'): opciones.append(f"Hielo: {data['hielo']}")
            if opciones: nombre_completo += f" ({' + '.join(opciones)})"
            items.append({
                'llave': llave,
                'nombre': nombre_completo,
                'precio': float(precio_final),
                'cantidad': data['cantidad'],
                'subtotal': float(sub)
            })
        except Producto.DoesNotExist:
            pass
    return JsonResponse({'items': items, 'total_general': total_general})
def sumar_carrito(request, llave):
    carrito = obtener_carrito_seguro(request)
    if llave in carrito:
        carrito[llave]['cantidad'] += 1
        request.session['carrito'] = carrito
        request.session.modified = True
    total_items = sum(item['cantidad'] for item in carrito.values()) if carrito else 0
    return JsonResponse({'status': 'ok', 'total_items': total_items})
def restar_del_carrito(request, llave):
    carrito = obtener_carrito_seguro(request)
    if llave in carrito:
        if carrito[llave]['cantidad'] > 1:
            carrito[llave]['cantidad'] -= 1
        else:
            del carrito[llave]
        request.session['carrito'] = carrito
        request.session.modified = True
    total_items = sum(item['cantidad'] for item in carrito.values()) if carrito else 0
    return JsonResponse({'status': 'ok', 'total_items': total_items})
def eliminar_del_carrito(request, llave):
    carrito = obtener_carrito_seguro(request)
    if llave in carrito:
        del carrito[llave]
        request.session['carrito'] = carrito
        request.session.modified = True
    total_items = sum(item['cantidad'] for item in carrito.values()) if carrito else 0
    return JsonResponse({'status': 'ok', 'total_items': total_items})
def limpiar_carrito(request):
    if 'carrito' in request.session:
        del request.session['carrito']
        request.session.modified = True
    return JsonResponse({'status': 'ok', 'mensaje': 'Carrito vaciado'})
# ==========================================================================
# MÓDULO 3: CHECKOUT, BASE DE DATOS Y PAGOS
# ==========================================================================

def procesar_pedido(request):
    config = obtener_configuracion()
    if not pedidos_online_habilitados(config):
        return JsonResponse({'status': 'error', 'mensaje': 'Los pedidos por el celular estan desactivados por alta demanda.'})
    carrito = obtener_carrito_seguro(request)
    if not carrito: return JsonResponse({'status': 'error', 'mensaje': 'El carrito está vacío'})
    nombre = request.POST.get('nombre_cliente', '')
    telefono = request.POST.get('telefono_cliente', '')
    pago = request.POST.get('tipo_pago', 'mercadopago')
    if pago == 'mercadopago' and not os.environ.get('MP_ACCESS_TOKEN'):
        return JsonResponse({'status': 'error', 'mensaje': 'Mercado Pago no está configurado en el servidor.'}, status=503)
    tipo_entrega = request.POST.get('tipo_entrega', 'mostrador')
    numero_mesa = request.POST.get('numero_mesa', '')
    puesto_slug = request.session.get('puesto_carrito')
    punto_venta = PuntoVenta.objects.filter(slug=puesto_slug).first() if puesto_slug else None
    estado_inicial = 'pendiente'
    pedido = Pedido.objects.create(
        estado=estado_inicial, total=0, nombre_cliente=nombre, telefono_cliente=telefono,
        tipo_entrega=tipo_entrega, numero_mesa=numero_mesa, tipo_pago=pago, punto_venta=punto_venta
    )
    total_pedido = 0
    for llave, data in carrito.items():
        prod = get_object_or_404(Producto, id=int(data['producto_id']))
        total_extras = 0
        opciones_elegidas = ['variante', 'guarnicion', 'punto', 'relleno', 'salsa', 'adicional', 'hielo']
        for clave in opciones_elegidas:
            texto_opcion = data.get(clave, '')
            if texto_opcion:
                if "(+" in texto_opcion:
                    precios_pos = re.findall(r'\(\+(\d+(?:\.\d+)?)\)', texto_opcion)
                    for p in precios_pos:
                        total_extras += float(p)
                if "(-" in texto_opcion:
                    precios_neg = re.findall(r'\(\-(\d+(?:\.\d+)?)\)', texto_opcion)
                    for n in precios_neg:
                        total_extras -= float(n)
        precio_final_item = float(prod.precio) + total_extras
        total_pedido += precio_final_item * data['cantidad']
        DetallePedido.objects.create(
            pedido=pedido, producto=prod, cantidad=data['cantidad'], precio_unitario=precio_final_item,
            variante_elegida=data.get('variante', ''), guarnicion_elegida=data.get('guarnicion', ''),
            punto_coccion_elegido=data.get('punto', ''), relleno_elegido=data.get('relleno', ''),
            salsa_elegida=data.get('salsa', ''), adicional_elegido=data.get('adicional', ''),
            hielo_elegido=data.get('hielo', '')
        )
    # Descuento en efectivo configurable desde el panel.
    if pago == 'efectivo' and descuento_efectivo_vigente(config):
        porcentaje = float(getattr(config, 'descuento_efectivo_porcentaje', 10) or 0)
        total_pedido = float(total_pedido) * (1 - (porcentaje / 100))
    pedido.total = total_pedido
    pedido.save()
    request.session['carrito'] = {}
    request.session.modified = True
    mp_id = None
    nave_url = None
    if pago == 'mercadopago':
        try:
            sdk = mercadopago.SDK(os.environ["MP_ACCESS_TOKEN"])
            host = request.get_host()
            preference_data = {
                "items": [{"title": f"Pedido #{pedido.id}", "quantity": 1, "unit_price": float(pedido.total)}],
                "back_urls": {
                    "success": f"https://{host}/exito/{pedido.id}/",
                    "failure": f"https://{host}/",
                    "pending": f"https://{host}/exito/{pedido.id}/"
                },
                "auto_return": "approved", "external_reference": str(pedido.id),
                "notification_url": f"https://{host}/webhook-mp/"
            }
            res = sdk.preference().create(preference_data)
            mp_id = res.get("response", {}).get("id")
        except Exception as e: print(f"Error MP: {e}")
    elif pago == 'nave':
        try:
            host = request.get_host()
            TOKEN_NAVE = "TU_TOKEN_SECRETO_DE_NAVE_ACA"
            headers = {
                "Authorization": f"Bearer {TOKEN_NAVE}",
                "Content-Type": "application/json"
            }
            payload = {
                "external_reference": str(pedido.id),
                "title": f"{settings.RESTAURANT_NAME} - Pedido #{pedido.id}",
                "total_amount": float(pedido.total),
                "currency": "ARS",
                "webhook_url": f"https://{host}/webhook-nave/",
                "success_url": f"https://{host}/exito-nave/{pedido.id}/"
            }
            url_api_nave = "https://api.nave.mobi/v1/checkout"
            res_nave = requests.post(url_api_nave, json=payload, headers=headers, timeout=10)
            if res_nave.status_code in [200, 201]:
                datos_nave = res_nave.json()
                nave_url = datos_nave.get("checkout_url")
            else:
                print(f"Error en API Nave: {res_nave.text}")
        except Exception as e:
            print(f"Error de conexión con Nave: {e}")
    return JsonResponse({
        'status': 'ok',
        'pedido_id': pedido.id,
        'mp_id': mp_id,
        'nave_url': nave_url
    })
@csrf_exempt
def webhook_mercadopago(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            if data.get("action") == "payment.created" or data.get("type") == "payment":
                payment_id = data.get("data", {}).get("id")
                token_mp = os.environ.get("MP_ACCESS_TOKEN", "")
                if not token_mp:
                    return JsonResponse({'error': 'Mercado Pago no configurado'}, status=503)
                headers = {"Authorization": f"Bearer {token_mp}"}
                mp_response = requests.get(f"https://api.mercadopago.com/v1/payments/{payment_id}", headers=headers)
                pago_info = mp_response.json()
                if pago_info.get("status") == "approved":
                    pedido_id = pago_info.get("external_reference")
                    pedido = Pedido.objects.get(id=pedido_id)
                    if pedido.estado == 'pendiente':
                        pedido.estado = 'preparacion'
                        pedido.mercado_pago_id = str(payment_id)
                        pedido.save()
            return JsonResponse({"status": "ok"}, status=200)
        except Exception as e: return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Método no permitido"}, status=405)
def pago_exitoso(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    return render(request, 'pedidos/seguimiento.html', {'pedido': pedido})
@csrf_exempt
def webhook_nave(request):
    if request.method == 'POST':
        return JsonResponse({"status": "ok"}, status=200)
    return JsonResponse({"error": "Método no permitido"}, status=405)
def pago_exitoso_nave(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    return render(request, 'pedidos/seguimiento.html', {'pedido': pedido})
# ==========================================================================
# MÓDULO 4: PANEL DE CONTROL DE ADMINISTRACIÓN
# ==========================================================================

def login_dashboard(request):
    # La entrada desde el icono del escritorio debe seguir al Salon despues del PIN.
    # Solo aceptar una ruta interna fija, sin redirecciones abiertas.
    destino = request.GET.get('next') or request.POST.get('next')
    destino_salon = destino == reverse('pedidos:salon')
    if request.session.get('dashboard_auth'):
        return redirect('pedidos:salon' if destino_salon else 'pedidos:panel_control')
    if request.method == 'POST':
        if settings.PANEL_PIN and secrets.compare_digest(str(request.POST.get('pin', '')), settings.PANEL_PIN):
            request.session['dashboard_auth'] = True
            request.session.set_expiry(0)
            return redirect('pedidos:salon' if destino_salon else 'pedidos:panel_control')
        else:
            messages.error(request, "PIN incorrecto. Acceso denegado.")
    return render(request, 'pedidos/login_dashboard.html', {'destino_salon': destino_salon})


def _redirect_tab_cuentas(cuenta_id=None):
    url = reverse('pedidos:panel_control') + '?tab=cuentas'
    if cuenta_id:
        url += f'#cuenta-{cuenta_id}'
    else:
        url += '#tab-cuentas'
    return redirect(url)


def _decimal_desde_form(valor):
    valor = str(valor or '').strip().replace('$', '').replace(' ', '')
    if not valor:
        return Decimal('0.00')
    if ',' in valor and '.' in valor:
        valor = valor.replace('.', '').replace(',', '.')
    else:
        valor = valor.replace(',', '.')
    return Decimal(valor)


def _preparar_cuentas_corrientes():
    cuentas = list(
        CuentaCorriente.objects
        .prefetch_related('movimientos__comprobante_pos')
        .all()
    )
    # Orden A-Z independientemente de tildes y mayúsculas.
    cuentas.sort(
        key=lambda c: (
            ''.join(
                letra for letra in unicodedata.normalize('NFD', c.nombre.casefold())
                if not unicodedata.combining(letra)
            ),
            c.pk,
        )
    )

    total_deuda = Decimal('0.00')
    total_favor = Decimal('0.00')

    for cuenta in cuentas:
        saldo = sum((movimiento.monto for movimiento in cuenta.movimientos.all()), Decimal('0.00'))
        cuenta.saldo_panel = saldo
        cuenta.saldo_abs = abs(saldo)

        if saldo < 0:
            cuenta.estado_panel = 'Debe'
            cuenta.estado_clase = 'debe'
            total_deuda += abs(saldo)
        elif saldo > 0:
            cuenta.estado_panel = 'A favor'
            cuenta.estado_clase = 'favor'
            total_favor += saldo
        else:
            cuenta.estado_panel = 'Al día'
            cuenta.estado_clase = 'aldia'

    return cuentas, total_deuda, total_favor

def panel_control(request):
    if not request.session.get('dashboard_auth'):
        return redirect('pedidos:login_dashboard')
    Categoria.objects.get_or_create(nombre='Salon')
    config = obtener_configuracion()
    # En Pedidos solo se muestran pedidos de la web y mostradores;
    # las mesas cobradas en POS siguen guardadas para ventas y cierre de caja.
    pedidos = (
        pedidos_del_panel()
        .exclude(
            Q(tipo_pago__in=['mercadopago', 'nave'])
            & Q(estado='pendiente')
        )
        .order_by('-fecha_creacion')
    )
    productos = Producto.objects.all().order_by('categoria__nombre', 'orden', 'nombre')
    filtro_categoria = request.GET.get('categoria')
    filtro_puesto = request.GET.get('puesto')
    if filtro_categoria:
        productos = productos.filter(categoria__id=filtro_categoria)
    if filtro_puesto:
        productos = productos.filter(puntos_venta__id=filtro_puesto)

    opiniones = OpinionCliente.objects.all().order_by('-fecha_creacion')
    opiniones_no_leidas = opiniones.filter(leida=False).count()
    cuentas_corrientes, cuentas_total_deuda, cuentas_total_favor = _preparar_cuentas_corrientes()

    hoy = timezone.localdate()
    pedidos_hoy = (
        Pedido.objects
        .filter(fecha_creacion__date=hoy, archivado_ventas=False)
        .exclude(tipo_pago='ticket_salon_temporal')
    )

    ventas_hoy_total = (
        pedidos_hoy
        .filter(Q(estado__in=['listo', 'entregado']) | Q(tipo_entrega='para_llevar', tipo_pago__in=['efectivo', 'debito', 'mercadopago']))
        .exclude(tipo_pago='pendiente_para_llevar')
        .aggregate(total=Sum('total'))
        .get('total')
        or 0
    )

    pedidos_pendientes_count = pedidos.filter(estado='pendiente').count()
    pedidos_preparacion_count = pedidos.filter(estado='preparacion').count()
    pedidos_listos_count = pedidos.filter(estado='listo').count()
    productos_activos_count = Producto.objects.filter(disponible=True).count()
    productos_pausados_count = Producto.objects.filter(disponible=False).count()

    return render(request, 'pedidos/panel.html', {
        'pedidos': pedidos,
        'productos': productos,
        'puestos': PuntoVenta.objects.all(),
        'categorias': Categoria.objects.all(),
        'filtro_categoria': filtro_categoria,
        'filtro_puesto': filtro_puesto,
        'buffet_habilitado': config.buffet_habilitado,
        'opiniones': opiniones,
        'opiniones_no_leidas': opiniones_no_leidas,
        'cuentas_corrientes': cuentas_corrientes,
        'cuentas_total_deuda': cuentas_total_deuda,
        'cuentas_total_favor': cuentas_total_favor,
        'mozos': Mozo.objects.all().order_by('nombre'),
        'configuracion': config,
        'salon_habilitado': getattr(config, 'salon_habilitado', True),
        'welcome_image_available': bienvenida_disponible(),
        'welcome_image_url': bienvenida_popup_url(),
        'welcome_images': bienvenida_popup_urls(),
        'ventas_hoy_total': ventas_hoy_total,
        'pedidos_pendientes_count': pedidos_pendientes_count,
        'pedidos_preparacion_count': pedidos_preparacion_count,
        'pedidos_listos_count': pedidos_listos_count,
        'productos_activos_count': productos_activos_count,
        'productos_pausados_count': productos_pausados_count,
    })


def cuentas_ventana_salon(request):
    """Cuentas corrientes embebidas en ventana de Salon: no carga el dashboard completo."""
    if not request.session.get('dashboard_auth'):
        return redirect('pedidos:login_dashboard')
    cuentas, total_deuda, total_favor = _preparar_cuentas_corrientes()
    return render(request, 'pedidos/cuentas_ventana.html', {
        'cuentas_corrientes': cuentas,
        'cuentas_total_deuda': total_deuda,
        'cuentas_total_favor': total_favor,
    })


def crear_cuenta_corriente(request):
    sin_acceso = _acceso_cuentas(request)
    if sin_acceso is not None:
        return sin_acceso
    if request.method != 'POST':
        return _redirect_tab_cuentas()

    nombre = request.POST.get('nombre', '').strip()
    telefono = request.POST.get('telefono', '').strip()
    nota = request.POST.get('nota', '').strip()
    saldo_inicial = request.POST.get('saldo_inicial', '').strip()
    estado_inicial = request.POST.get('estado_inicial', 'debe')

    if not nombre:
        return _error_cuentas(request, 'Ingresá el nombre de la persona.')
    try:
        monto = abs(_decimal_desde_form(saldo_inicial))
        if not monto.is_finite() or monto > Decimal('9999999999.99'):
            raise ValueError('Monto fuera de rango')
    except (InvalidOperation, ValueError):
        return _error_cuentas(request, 'Ingresá un monto inicial válido.')

    with transaction.atomic():
        cuenta = CuentaCorriente.objects.create(nombre=nombre, telefono=telefono, nota=nota)
        if monto > 0:
            if estado_inicial == 'favor':
                monto_final, tipo, descripcion = monto, 'favor', 'Saldo inicial a favor'
            else:
                monto_final, tipo, descripcion = -monto, 'consumo', 'Deuda inicial'
            MovimientoCuentaCorriente.objects.create(
                cuenta=cuenta, tipo=tipo, descripcion=descripcion, monto=monto_final,
            )
    return _ok_cuentas(request, f'Cuenta creada para {cuenta.nombre}.', cuenta.id)




def agregar_movimiento_cuenta(request, cuenta_id):
    sin_acceso = _acceso_cuentas(request)
    if sin_acceso is not None:
        return sin_acceso
    if request.method != 'POST':
        return _redirect_tab_cuentas()

    tipo_form = request.POST.get('tipo', 'consumo')
    descripcion = request.POST.get('descripcion', '').strip()
    try:
        monto = abs(_decimal_desde_form(request.POST.get('monto', '0')))
    except (InvalidOperation, ValueError):
        return _error_cuentas(request, 'Ingresá un monto válido.', cuenta_id)
    if not monto.is_finite() or monto <= 0 or monto > Decimal('9999999999.99'):
        return _error_cuentas(request, 'El monto debe ser mayor a cero y válido.', cuenta_id)

    if tipo_form == 'consumo':
        monto_final, tipo = -monto, 'consumo'
        descripcion = descripcion or 'Consumo manual'
    elif tipo_form == 'pago':
        monto_final, tipo = monto, 'pago'
        descripcion = descripcion or 'Pago recibido'
    elif tipo_form == 'favor':
        monto_final, tipo = monto, 'favor'
        descripcion = descripcion or 'Dinero a favor'
    elif tipo_form == 'ajuste_debe':
        monto_final, tipo = -monto, 'ajuste'
        descripcion = descripcion or 'Ajuste: debe'
    elif tipo_form == 'ajuste_favor':
        monto_final, tipo = monto, 'ajuste'
        descripcion = descripcion or 'Ajuste: a favor'
    else:
        return _error_cuentas(request, 'Tipo de movimiento inválido.', cuenta_id)

    with transaction.atomic():
        cuenta = get_object_or_404(CuentaCorriente.objects.select_for_update(), id=cuenta_id)
        MovimientoCuentaCorriente.objects.create(
            cuenta=cuenta, tipo=tipo, descripcion=descripcion, monto=monto_final,
        )
    return _ok_cuentas(request, f'Movimiento agregado a {cuenta.nombre}.', cuenta.id)




def eliminar_movimiento_cuenta(request, movimiento_id):
    sin_acceso = _acceso_cuentas(request)
    if sin_acceso is not None:
        return sin_acceso
    if request.method != 'POST':
        return _redirect_tab_cuentas()
    with transaction.atomic():
        # La cuenta se bloquea antes de eliminar, igual que al saldarla.
        movimiento_original = get_object_or_404(MovimientoCuentaCorriente, id=movimiento_id)
        cuenta = get_object_or_404(CuentaCorriente.objects.select_for_update(), pk=movimiento_original.cuenta_id)
        movimiento = get_object_or_404(MovimientoCuentaCorriente, id=movimiento_id, cuenta=cuenta)
        movimiento.delete()
    return _ok_cuentas(request, f'Movimiento eliminado de {cuenta.nombre}.', cuenta.id)




def eliminar_cuenta_corriente(request, cuenta_id):
    sin_acceso = _acceso_cuentas(request)
    if sin_acceso is not None:
        return sin_acceso
    if request.method != 'POST':
        return _redirect_tab_cuentas()
    with transaction.atomic():
        cuenta = get_object_or_404(CuentaCorriente.objects.select_for_update(), id=cuenta_id)
        nombre = cuenta.nombre
        cuenta.delete()
    return _ok_cuentas(request, f'Cuenta eliminada: {nombre}.', cuenta_id, eliminado=True)



def agregar_producto(request):
    # La categoría Salon siempre debe existir para los productos internos del POS.
    Categoria.objects.get_or_create(nombre='Salon')

    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)

        if form.is_valid():
            producto_nuevo = form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'ok',
                    'mensaje': 'Producto agregado correctamente.',
                    'producto': {
                        'id': producto_nuevo.pk,
                        'codigo': producto_nuevo.codigo_rapido or str(producto_nuevo.pk),
                        'nombre': producto_nuevo.nombre,
                        'precio': str(producto_nuevo.precio),
                        'disponible': producto_nuevo.disponible,
                        'es_salon': producto_nuevo.categoria.nombre == 'Salon',
                    },
                })
            messages.success(
                request,
                'Producto guardado. Podés cargar otro sin salir de esta pantalla.'
            )

            # Después de guardar vuelve al mismo formulario vacío.
            # Esto agiliza la carga de varios productos seguidos.
            return redirect('pedidos:agregar_producto')
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            errores = [f'{campo}: {msg}' for campo, mensajes in form.errors.items() for msg in mensajes]
            return JsonResponse({'status': 'error', 'mensaje': ' | '.join(errores) or 'Revisá los campos.'}, status=400)
    else:
        form = ProductoForm()

    return render(request, 'pedidos/formulario_producto.html', {
        'form': form,
        'accion': 'Agregar Nuevo Producto'
    })


def editar_producto(request, producto_id):
    Categoria.objects.get_or_create(nombre='Salon')
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'ok', 'producto': {'id': producto.pk, 'nombre': producto.nombre}})
            return redirect('pedidos:panel_control')
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            errores = []
            for campo, mensajes in form.errors.items():
                for mensaje in mensajes:
                    errores.append(f'{campo}: {mensaje}')
            return JsonResponse({
                'status': 'error',
                'mensaje': ' | '.join(errores) or 'Revisá los datos del producto.'
            }, status=400)
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'pedidos/formulario_producto.html', {
        'form': form,
        'accion': f'Editar: {producto.nombre}',
        'producto': producto
    })


def eliminar_producto(request, producto_id):
    get_object_or_404(Producto, id=producto_id).delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest': return JsonResponse({'status': 'ok'})
    return redirect('pedidos:panel_control')
def editar_precio(request, producto_id):
    if request.method == 'POST':
        prod = get_object_or_404(Producto, id=producto_id)
        precio_limpio = request.POST.get('precio', '').replace(',', '.')
        prod.precio = precio_limpio
        prod.save()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok'})
    return redirect('pedidos:panel_control')
def cambiar_estado_puesto(request, puesto_id):
    puesto = get_object_or_404(PuntoVenta, id=puesto_id)
    puesto.abierto = not puesto.abierto
    puesto.save()
    return JsonResponse({'esta_abierto': puesto.abierto})
def cambiar_disponibilidad(request, producto_id):
    prod = get_object_or_404(Producto, id=producto_id)
    prod.disponible = not prod.disponible
    prod.save()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest': return JsonResponse({'status': 'ok', 'disponible': prod.disponible})
    return redirect('pedidos:panel_control')
def eliminar_pedido(request, pedido_id):
    get_object_or_404(Pedido, id=pedido_id).delete()
    return redirect('pedidos:panel_control')
def eliminar_item_pedido(request, item_id):
    item = get_object_or_404(DetallePedido, id=item_id)
    pedido = item.pedido
    item.delete()
    nuevo_total = sum((i.cantidad * i.precio_unitario) for i in pedido.items.all())
    if nuevo_total == 0: pedido.delete()
    else:
        pedido.total = nuevo_total
        pedido.save()
    return redirect('pedidos:panel_control')
def actualizar_producto_puestos(request, producto_id):
    if request.method == 'POST': get_object_or_404(Producto, id=producto_id).puntos_venta.set(request.POST.getlist('puestos'))
    return redirect('pedidos:panel_control')
def cambiar_estado_pedido(request, pedido_id, nuevo_estado):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    pedido.estado = nuevo_estado
    if nuevo_estado == 'preparacion':
        pedido.impreso_caja = False
        cache.delete(f'solo_cuenta_{pedido.id}')
    pedido.save()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest': return JsonResponse({'status': 'ok', 'estado': nuevo_estado})
    return redirect('pedidos:panel_control')
def eliminar_todo_historial(request):
    # Compatibility for old bookmarked route: NEVER delete order history on GET.
    # Reset uses a POST+CSRF+explicit confirmation, keeping originals for audit.
    return reiniciar_historial_ventas(request)



# ==========================================================================
# MOZOS / PERSONAL DE SALÓN
# ==========================================================================

def agregar_mozo(request):
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status': 'error', 'mensaje': 'No autorizado'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=405)

    nombre = request.POST.get('nombre', '').strip()
    if len(nombre) < 2:
        return JsonResponse({'status': 'error', 'mensaje': 'Ingresá un nombre válido.'}, status=400)

    if Mozo.objects.filter(nombre__iexact=nombre).exists():
        return JsonResponse({'status': 'error', 'mensaje': 'Ese mozo ya está cargado.'}, status=400)

    mozo = Mozo.objects.create(nombre=nombre[:100])

    return JsonResponse({
        'status': 'ok',
        'mozo': {
            'id': mozo.id,
            'nombre': mozo.nombre,
            'eliminar_url': f'/dashboard/mozo/{mozo.id}/eliminar/'
        }
    })




def eliminar_mozo(request, mozo_id):
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status': 'error', 'mensaje': 'No autorizado'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=405)

    mozo = get_object_or_404(Mozo, id=mozo_id)
    nombre = mozo.nombre
    mozo.delete()

    return JsonResponse({'status': 'ok', 'nombre': nombre})




# ==========================================================================
# OPINIONES PRIVADAS DE CLIENTES
# ==========================================================================

def enviar_opinion(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=405)

    mesa = request.POST.get('mesa', '').strip()
    nombre = request.POST.get('nombre', '').strip()
    mozo = request.POST.get('mozo', '').strip()
    mensaje = request.POST.get('mensaje', '').strip()

    if not mesa:
        return JsonResponse({'status': 'error', 'mensaje': 'Ingresá el número de mesa.'}, status=400)
    if not nombre:
        return JsonResponse({'status': 'error', 'mensaje': 'Ingresá tu nombre.'}, status=400)
    if not mozo:
        return JsonResponse({'status': 'error', 'mensaje': 'Indicá qué mozo te atendió.'}, status=400)
    if len(mensaje) < 3:
        return JsonResponse({'status': 'error', 'mensaje': 'Escribí tu opinión para poder enviarla.'}, status=400)

    OpinionCliente.objects.create(
        tipo='atencion',
        mensaje=mensaje[:1000],
        mesa=mesa[:20],
        nombre=nombre[:100],
        mozo=mozo[:100]
    )

    return JsonResponse({'status': 'ok'})


def marcar_opinion_leida(request, opinion_id):
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status': 'error', 'mensaje': 'No autorizado'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=405)

    opinion = get_object_or_404(OpinionCliente, id=opinion_id)
    opinion.leida = True
    opinion.save(update_fields=['leida'])
    return JsonResponse({'status': 'ok'})


def eliminar_opinion(request, opinion_id):
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status': 'error', 'mensaje': 'No autorizado'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=405)

    opinion = get_object_or_404(OpinionCliente, id=opinion_id)
    opinion.delete()
    return JsonResponse({'status': 'ok'})

# ==========================================================================
# MÓDULO 5: API PARA LA TICKETERA LOCAL (IMPRESORA) Y PANTALLA ESTADO
# ==========================================================================

def _opcion_sin_precio_cocina(texto):
    """Quita SOLO modificadores de importe del menú, sin perder variantes o puntos.

    Ej.: 'Napolitana (+2500)' -> 'Napolitana'. No cambia el precio real
    guardado en DetallePedido ni las opciones mostradas al operador/caja.
    """
    import re
    return re.sub(r'\s*\(\s*[+-]\s*\$?\s*\d+(?:[.,]\d{1,2})?\s*\)', '',
                  str(texto or '')).strip()


def api_pedidos_pendientes(request):
    pedidos_nuevos = Pedido.objects.filter(
        Q(estado__in=['preparacion', 'listo']) | Q(estado='pendiente', tipo_pago='efectivo'),
        impreso_caja=False
    ).prefetch_related('items__producto__categoria').select_related('para_llevar')
    data = []
    for p in pedidos_nuevos:
        es_para_llevar = p.tipo_entrega == 'para_llevar'
        items_cocina = []
        items_barra = []
        items_caja = []
        for item in p.items.all():
            detalle_texto = item.producto.nombre
            ops = []
            if getattr(item, 'variante_elegida', None): ops.append(item.variante_elegida)
            if getattr(item, 'guarnicion_elegida', None): ops.append(item.guarnicion_elegida)
            if getattr(item, 'punto_coccion_elegido', None): ops.append(f"Punto: {item.punto_coccion_elegido}")
            if getattr(item, 'relleno_elegido', None): ops.append(f"Relleno: {item.relleno_elegido}")
            if getattr(item, 'salsa_elegida', None): ops.append(f"Salsa: {item.salsa_elegida}")
            if getattr(item, 'adicional_elegido', None): ops.append(f"Extra: {item.adicional_elegido}")
            if getattr(item, 'hielo_elegido', None): ops.append(f"Hielo: {item.hielo_elegido}")
            texto_opciones = f" ({' | '.join(ops)})" if ops else ""
            descripcion_completa = f"{item.cantidad}x {detalle_texto}{texto_opciones}"
            subtotal_item = item.cantidad * item.precio_unitario
            items_caja.append({
                'descripcion': descripcion_completa,
                'subtotal': f"${subtotal_item:.2f}"
            })
            # La comanda de preparación NO transporta importes. Los números
            # entre paréntesis son suplementos del menú, no instrucciones para cocina.
            ops_cocina = [_opcion_sin_precio_cocina(op) for op in ops]
            ops_cocina = [op for op in ops_cocina if op]
            item_data = {'nombre': detalle_texto + (f" ({' | '.join(ops_cocina)})" if ops_cocina else ''),
                         'cantidad': item.cantidad, 'plato': detalle_texto,
                         'opciones': ops_cocina,
                         'aviso_celiaco': bool(item.aviso_celiaco)}
            cat_nombre = item.producto.categoria.nombre.lower() if item.producto and item.producto.categoria else ""
            if not es_para_llevar and ("bebida" in cat_nombre or "cafe" in cat_nombre or "café" in cat_nombre or "cafeteria" in cat_nombre):
                items_barra.append(item_data)
            else:
                items_cocina.append(item_data)
        hora_pedido = localtime(p.fecha_creacion).strftime('%H:%M')
        alerta_celiaco = any(i['aviso_celiaco'] for i in (items_cocina + items_barra))
        notas_llevar = ''
        if es_para_llevar:
            meta = getattr(p, 'para_llevar', None)
            notas_llevar = meta.observaciones if meta else ''
        es_ticket_salon = (p.tipo_pago == 'ticket_salon_temporal')
        es_solo_cuenta = cache.get(f'solo_cuenta_{p.id}') or es_ticket_salon
        if es_solo_cuenta:
            items_cocina = []
            items_barra = []
            imprimir_cobro = True
        elif p.tipo_pago == 'efectivo' and p.estado == 'pendiente':
            items_cocina = []
            items_barra = []
            imprimir_cobro = True
        else:
            imprimir_cobro = False
        nombre_final = p.nombre_cliente or "Sin Nombre"
        if getattr(p, 'mozo', ''):
            nombre_final += f" · Mozo: {p.mozo}"
        if p.telefono_cliente:
            nombre_final += f" (Tel: {p.telefono_cliente})"
        data.append({
            'id': p.id,
            'hora': hora_pedido,
            'cliente': nombre_final,
            'notas': notas_llevar,
            'alerta_celiaco': alerta_celiaco,
            'entrega': p.tipo_entrega.upper() if p.tipo_entrega else "MOSTRADOR",
            'mesa': p.numero_mesa if p.numero_mesa else '-',
            # La ticketera imprime MOZO con pedido['mozo']. Sin este campo
            # usaba siempre su valor de respaldo "CAJA", aunque la mesa
            # tuviera un mozo seleccionado y guardado en la base.
            'mozo': str(getattr(p, 'mozo', '') or '').strip(),
            'pago': ('NO PAGADO' if p.tipo_pago == 'pendiente_para_llevar' else p.tipo_pago.upper() if p.tipo_pago else 'EFECTIVO'),
            'total': f"${p.total:.2f}",
            'imprimir_ticket_cobro': imprimir_cobro,
            'items_caja': items_caja,
            'items_cocina': items_cocina,
            'items_barra': items_barra
        })
    return JsonResponse({'status': 'ok', 'pedidos': data})


@csrf_exempt
def api_marcar_impreso(request, pedido_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'})
    try:
        pedido = Pedido.objects.get(id=pedido_id)
        # Los pedidos creados por el POS de Salón se usan únicamente como
        # cola de impresión y no deben aparecer en historial/cierre de caja.
        if pedido.tipo_pago == 'ticket_salon_temporal':
            # SANMARTIN_V150_ESTADO_TICKET: estado persistente en PostgreSQL.
            # El ticket temporal NO es una venta; los reportes ya lo excluyen.
            # No se borra para permitir verificar cuándo la ticketera confirmó.
            pedido.impreso_caja = True
            pedido.save(update_fields=['impreso_caja'])
            cache.delete(f'solo_cuenta_{pedido_id}')
            return JsonResponse({'status': 'ok'})
        pedido.impreso_caja = True
        pedido.save()
        cache.delete(f'solo_cuenta_{pedido_id}')
        return JsonResponse({'status': 'ok'})
    except Pedido.DoesNotExist:
        return JsonResponse({'status': 'error', 'mensaje': 'Pedido no encontrado'})


def estado_pedido_api(request, pedido_id):
    try:
        pedido = Pedido.objects.get(id=pedido_id)
        return JsonResponse({
            'success': True,
            'estado': pedido.estado,
            'tipo_entrega': pedido.tipo_entrega,
            'tipo_pago': pedido.tipo_pago
        })
    except Pedido.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Pedido no encontrado'})
def seguimiento_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    return render(request, 'pedidos/seguimiento.html', {'pedido': pedido})

@csrf_exempt
def actualizar_configuracion(request):
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status': 'error', 'mensaje': 'No autorizado. Volvé a iniciar sesión en el panel.'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=405)

    # Acepta FormData normal y también JSON por si el navegador no manda bien el form.
    if request.POST:
        campo = request.POST.get('campo', '').strip()
        valor = request.POST.get('valor', '').strip()
    else:
        try:
            payload = json.loads(request.body.decode('utf-8') or '{}')
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = {}
        campo = str(payload.get('campo', '')).strip()
        valor = str(payload.get('valor', '')).strip()

    # El estado online se cambia SOLO desde el panel por decision manual.
    # No permitir reactivar el cierre programado mediante llamadas antiguas.
    if campo in {'cierre_automatico_activo', 'hora_cierre'}:
        return JsonResponse({'status': 'error', 'mensaje': 'El cierre automatico esta deshabilitado: los pedidos se pausan solo manualmente.'}, status=400)
    if campo == 'buffet_habilitado' and getattr(settings, 'SM_LOCAL_MODE', False):
        return JsonResponse({'status': 'error', 'mensaje': 'El estado de pedidos web se cambia solamente desde el panel de Render, no en la caja local.'}, status=409)

    config = obtener_configuracion()

    campos_booleanos = {
        'buffet_habilitado',
        'descuento_efectivo_activo',
        'mostrar_promociones',
        'mostrar_opiniones',
        'mostrar_google_reviews',
        'mostrar_bienvenida',
        'salon_habilitado',
    }

    campos_actualizados = []

    if campo in campos_booleanos:
        setattr(config, campo, valor.lower() in {'1', 'true', 'on', 'yes', 'si', 'sí'})
        campos_actualizados.append(campo)

    elif campo == 'descuento_efectivo_porcentaje':
        try:
            config.descuento_efectivo_porcentaje = max(0, min(int(valor), 100))
        except (TypeError, ValueError):
            return JsonResponse({'status': 'error', 'mensaje': 'Ingresá un porcentaje válido.'}, status=400)
        campos_actualizados.append(campo)

    else:
        return JsonResponse({'status': 'error', 'mensaje': 'Configuración no permitida.'}, status=400)

    # Ningun proceso automatico altera buffet_habilitado.
    config.save(update_fields=campos_actualizados)
    config.refresh_from_db()

    if campo == 'hora_cierre':
        valor_respuesta = config.hora_cierre.strftime('%H:%M') if config.hora_cierre else ''
    else:
        valor_respuesta = getattr(config, campo)

    return JsonResponse({
        'status': 'ok',
        'mensaje': 'Configuración guardada.',
        'campo': campo,
        'valor': valor_respuesta,
        'buffet_habilitado': config.buffet_habilitado,
        'descuento_efectivo_activo': config.descuento_efectivo_activo,
        'descuento_efectivo_porcentaje': config.descuento_efectivo_porcentaje,
        'cierre_automatico_activo': False,
        'hora_cierre': config.hora_cierre.strftime('%H:%M') if config.hora_cierre else '',
        'mostrar_promociones': config.mostrar_promociones,
        'mostrar_opiniones': config.mostrar_opiniones,
        'mostrar_google_reviews': config.mostrar_google_reviews,
        'mostrar_bienvenida': config.mostrar_bienvenida,
        'salon_habilitado': config.salon_habilitado,
    })




@csrf_exempt
def subir_popup_bienvenida(request):
    if not request.session.get('dashboard_auth'):
        return redirect('pedidos:login_dashboard')

    if request.method != 'POST':
        return redirect('pedidos:panel_control')

    archivos = request.FILES.getlist('popup_bienvenida')

    if not archivos:
        messages.error(request, 'Seleccioná una o más imágenes para el popup.')
        return redirect('pedidos:panel_control')

    carpeta_popup = carpeta_popup_bienvenida()

    def slot_ocupado(slot):
        # Revisa por existencia real del archivo, no solo por la lista precargada.
        # Así, si ya existe bienvenida_popup_1.png, nunca se pisa al subir otra foto.
        for extension in POPUP_BIENVENIDA_EXTS:
            ruta_slot = os.path.join(
                carpeta_popup,
                f'bienvenida_popup_{slot}.{extension}'
            )
            if os.path.exists(ruta_slot):
                return True

        # Compatibilidad con el nombre viejo bienvenida_popup.ext.
        if slot == 1:
            for extension in POPUP_BIENVENIDA_EXTS:
                ruta_vieja = os.path.join(
                    carpeta_popup,
                    f'bienvenida_popup.{extension}'
                )
                if os.path.exists(ruta_vieja):
                    return True

        return False

    def proximo_slot_libre():
        for slot in range(1, POPUP_BIENVENIDA_MAX + 1):
            if not slot_ocupado(slot):
                return slot
        return None

    # Validamos todo antes de guardar para no dejar cargas a medias.
    for archivo in archivos:
        extension = os.path.splitext(archivo.name)[1].lower().replace('.', '')

        if extension not in set(POPUP_BIENVENIDA_EXTS):
            messages.error(request, 'Usá imágenes JPG, PNG o WEBP.')
            return redirect('pedidos:panel_control')

        if archivo.size > 5 * 1024 * 1024:
            messages.error(request, 'Cada imagen no puede pesar más de 5 MB.')
            return redirect('pedidos:panel_control')

    guardadas = 0

    for archivo in archivos:
        slot = proximo_slot_libre()

        if not slot:
            messages.error(
                request,
                f'Ya tenés {POPUP_BIENVENIDA_MAX} imágenes. Eliminá una antes de subir otra.'
            )
            return redirect('pedidos:panel_control')

        extension = os.path.splitext(archivo.name)[1].lower().replace('.', '')
        nombre_final = f'bienvenida_popup_{slot}.{extension}'
        ruta_final = os.path.join(carpeta_popup, nombre_final)

        # Importante: no borramos ni reemplazamos imágenes anteriores.
        # Solo guardamos en un slot vacío.
        with open(ruta_final, 'wb+') as destino:
            for chunk in archivo.chunks():
                destino.write(chunk)

        guardadas += 1

    config = obtener_configuracion()
    config.mostrar_bienvenida = True
    config.save(update_fields=['mostrar_bienvenida'])

    messages.success(
        request,
        f'{guardadas} imagen/es agregada/s al popup. Las anteriores se mantienen.'
    )
    return redirect('pedidos:panel_control')


@csrf_exempt
def eliminar_popup_bienvenida(request):
    if not request.session.get('dashboard_auth'):
        return redirect('pedidos:login_dashboard')

    if request.method != 'POST':
        return redirect('pedidos:panel_control')

    nombre_archivo = request.POST.get('archivo', '').strip()

    if nombre_archivo:
        limpiar_popup_bienvenida_media(nombre_archivo)
        messages.success(request, 'Imagen del popup eliminada.')
    else:
        limpiar_popup_bienvenida_media()
        messages.success(request, 'Todas las imágenes del popup fueron eliminadas.')

    config = obtener_configuracion()
    config.mostrar_bienvenida = bienvenida_disponible()
    config.save(update_fields=['mostrar_bienvenida'])

    return redirect('pedidos:panel_control')


def cambiar_estado_global(request):
    if not request.session.get('dashboard_auth'):
        return redirect('pedidos:login_dashboard')
    config = obtener_configuracion()
    config.buffet_habilitado = not config.buffet_habilitado
    config.save()
    return redirect('pedidos:panel_control')
def ticket_mesa(request, pedido_id):
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status': 'error', 'mensaje': 'No autorizado'})
    pedido = get_object_or_404(Pedido, id=pedido_id)
    cache.set(f'solo_cuenta_{pedido.id}', True, timeout=120)
    pedido.impreso_caja = False
    pedido.save()
    return JsonResponse({'status': 'ok'})
# ==========================================================================
# MÓDULO 6: BACKUP
# ==========================================================================

def descargar_backup_secreto(request):
    if not request.session.get('dashboard_auth'):
        raise Http404("No estás autorizado para descargar el respaldo.")
    base_dir = settings.BASE_DIR
    json_path = os.path.join(base_dir, 'backup_automatico.json')
    tar_path = os.path.join(base_dir, 'backup_completo.tar.gz')
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            call_command('dumpdata', 'pedidos', indent=4, stdout=f)
        with tarfile.open(tar_path, "w:gz") as tar:
            if os.path.exists(os.path.join(base_dir, 'media')):
                tar.add(os.path.join(base_dir, 'media'), arcname='media')
            if os.path.exists(json_path):
                tar.add(json_path, arcname='backup.json')
        if os.path.exists(tar_path):
            with open(tar_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/x-tar")
                response['Content-Disposition'] = 'attachment; filename=backup_buffet_completo.tar.gz'
                return response
    except Exception as e:
        print(f"Error generando backup: {e}")
    raise Http404("Hubo un error al generar el archivo de respaldo.")
# ==========================================================================
# MÓDULO 7: CIERRE DE CAJA Y ESTADÍSTICAS POR MOSTRADOR
# ==========================================================================

def api_resumen_ventas(request):
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status': 'error', 'mensaje': 'No autorizado'})

    # Solo entran ventas reales. Los tickets temporales usados para imprimir
    # una cuenta del salón siguen quedando afuera del cierre.
    pedidos_validos = (
        Pedido.objects
        .exclude(estado='cancelado')
        .exclude(tipo_pago='ticket_salon_temporal')
        .exclude(tipo_pago='pendiente_para_llevar')
        .exclude(
            Q(tipo_pago__in=['mercadopago', 'nave'])
            & Q(estado='pendiente')
        )
    )

    datos_mostradores = []
    gran_total = Decimal('0.00')

    def agregar_bloque(nombre, pedidos_queryset):
        nonlocal gran_total
        if not pedidos_queryset.exists():
            return

        total_ventas = sum((pedido.total for pedido in pedidos_queryset), Decimal('0.00'))
        gran_total += total_ventas
        detalles = DetallePedido.objects.filter(pedido__in=pedidos_queryset).select_related('producto')
        productos_vendidos = {}

        for detalle in detalles:
            nombre_producto = detalle.producto.nombre if detalle.producto else 'Producto eliminado'
            productos_vendidos[nombre_producto] = productos_vendidos.get(nombre_producto, 0) + detalle.cantidad

        productos_ordenados = sorted(productos_vendidos.items(), key=lambda item: item[1], reverse=True)

        datos_mostradores.append({
            'nombre': nombre,
            'total_ventas': float(total_ventas),
            'cantidad_pedidos': pedidos_queryset.count(),
            'efectivo': float(sum(
                (pedido.total for pedido in pedidos_queryset if pedido.tipo_pago == 'efectivo'),
                Decimal('0.00')
            )),
            'mercadopago': float(sum(
                (pedido.total for pedido in pedidos_queryset if pedido.tipo_pago == 'mercadopago'),
                Decimal('0.00')
            )),
            'debito': float(sum(
                (pedido.total for pedido in pedidos_queryset if pedido.tipo_pago == 'debito'),
                Decimal('0.00')
            )),
            'productos': [
                {'nombre': nombre_producto, 'cantidad': cantidad}
                for nombre_producto, cantidad in productos_ordenados
            ]
        })

    for puesto in PuntoVenta.objects.all():
        agregar_bloque(puesto.nombre, pedidos_validos.filter(punto_venta=puesto))

    # Las ventas del POS de mesas aparecen separadas en el cierre principal.
    pedidos_salon = pedidos_validos.filter(
        punto_venta__isnull=True,
        tipo_entrega='mesa'
    )
    agregar_bloque('Salón / Mesas', pedidos_salon)

    pedidos_para_llevar = pedidos_validos.filter(
        punto_venta__isnull=True, tipo_entrega='para_llevar'
    )
    agregar_bloque('Para llevar', pedidos_para_llevar)

    pedidos_generales = (
        pedidos_validos
        .filter(punto_venta__isnull=True)
        .exclude(tipo_entrega__in=['mesa', 'para_llevar'])
    )
    agregar_bloque('General / Sin Asignar', pedidos_generales)

    return JsonResponse({
        'status': 'ok',
        'gran_total': float(gran_total),
        'mostradores': datos_mostradores
    })

# ===========================================================================
# MÓDULO 8: POS DE SALÓN
# ===========================================================================

from .salon_csv import leer_catalogo_salon, importar_catalogo_salon, ErrorCatalogoSalon


# SAN MARTIN - SALON POS UNIFICADO + COBRO A CUENTA + IMPRESION

def imprimir_ticket_salon(request):
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status': 'error', 'mensaje': 'No autorizado'}, status=403)
    if not obtener_configuracion().salon_habilitado:
        return JsonResponse({'status': 'error', 'mensaje': 'El módulo Salón / Mesas está desactivado.'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=405)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'status': 'error', 'mensaje': 'JSON inválido'}, status=400)
    mesa = str(payload.get('mesa', '')).strip()
    mozo = str(payload.get('mozo', '')).strip()
    items = payload.get('items', [])
    if not mesa:
        return JsonResponse({'status': 'error', 'mensaje': 'Falta el número de mesa'}, status=400)
    if not isinstance(items, list) or not items:
        return JsonResponse({'status': 'error', 'mensaje': 'No hay productos para imprimir'}, status=400)
    pedido = Pedido.objects.create(estado='preparacion', total=Decimal('0.00'), nombre_cliente=('POS SALON PARCIAL' if payload.get('tipo') == 'cuenta_parcial' else 'POS SALON'), tipo_entrega='mesa', numero_mesa=mesa, mozo=mozo[:100], tipo_pago='ticket_salon_temporal', impreso_caja=False)
    total_calculado = Decimal('0.00')
    detalles_creados = 0
    try:
        for item in items:
            if not isinstance(item, dict):
                continue
            producto = None
            producto_id = item.get('producto_id')
            codigo = str(item.get('codigo', '')).strip()
            if producto_id:
                try:
                    producto = Producto.objects.filter(id=int(producto_id)).first()
                except (TypeError, ValueError):
                    producto = None
            if producto is None and codigo:
                producto = Producto.objects.filter(codigo_rapido=codigo).first()
            if producto is None and codigo.isdigit():
                producto = Producto.objects.filter(id=int(codigo)).first()
            if producto is None:
                continue
            try:
                cantidad = int(item.get('cantidad', 1))
            except (TypeError, ValueError):
                cantidad = 1
            if cantidad < 1:
                cantidad = 1
            try:
                precio = Decimal(str(item.get('precio', producto.precio)))
            except (InvalidOperation, TypeError, ValueError):
                precio = Decimal(str(producto.precio))
            if precio < 0:
                precio = Decimal('0.00')
            DetallePedido.objects.create(pedido=pedido, producto=producto, cantidad=cantidad, precio_unitario=precio)
            total_calculado += precio * cantidad
            detalles_creados += 1
        if detalles_creados == 0:
            pedido.delete()
            return JsonResponse({'status': 'error', 'mensaje': 'No se pudo relacionar ningún producto con la base de datos.'}, status=400)
        pedido.total = total_calculado
        pedido.save(update_fields=['total'])
        return JsonResponse({'status': 'ok', 'ticket_id': pedido.id, 'mensaje': 'Ticket enviado a la cola de la caja.'})
    except Exception as error:
        pedido.delete()
        return JsonResponse({'status': 'error', 'mensaje': 'Error preparando el ticket: ' + str(error)}, status=500)




def _salon_items_pedidos_web():
    """Pedidos QR de mesa aún abiertos, en una sola consulta liviana.

    Importante: NO recortamos pedidos por fecha ni cantidad: un pedido sin
    cobrar nunca debe desaparecer del Salón por una optimización.
    """
    filas = (
        DetallePedido.objects.filter(
            pedido__tipo_entrega='mesa', pedido__tipo_pago='efectivo',
            cantidad__gt=0,
        )
        .exclude(pedido__numero_mesa__isnull=True)
        .exclude(pedido__numero_mesa__exact='')
        .exclude(pedido__estado__in=['cancelado', 'entregado'])
        .exclude(pedido__nombre_cliente__istartswith='POS SALON')
        .values(
            'id', 'pedido_id', 'pedido__numero_mesa', 'producto_id',
            'producto__codigo_rapido', 'producto__nombre',
            'precio_unitario', 'cantidad',
        )
        .order_by('pedido__fecha_creacion', 'pedido_id', 'id')
    )
    salida = []
    for fila in filas.iterator(chunk_size=500):
        mesa = str(fila['pedido__numero_mesa'] or '').strip()
        if not mesa.isdigit() or not 1 <= int(mesa) <= 100:
            continue
        pid_producto = fila['producto_id']
        salida.append({
            'mesa': str(int(mesa)), 'pedido_id': fila['pedido_id'],
            'detalle_id': fila['id'], 'producto_id': pid_producto or 0,
            'codigo': (fila['producto__codigo_rapido'] or str(pid_producto)) if pid_producto else '',
            'nombre': fila['producto__nombre'] if pid_producto else 'Producto eliminado',
            'precio': float(fila['precio_unitario']), 'cantidad': fila['cantidad'],
            'origen': 'web',
        })
    return salida


def salon_pedidos_web_api(request):
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status':'error', 'mensaje':'No autorizado'}, status=403)
    if not obtener_configuracion().salon_habilitado:
        return JsonResponse({'status':'error','mensaje':'Salón desactivado'}, status=403)
    if request.method != 'GET':
        return JsonResponse({'status':'error','mensaje':'Método no permitido'}, status=405)
    respuesta = JsonResponse({'status':'ok','items':_salon_items_pedidos_web()})
    respuesta['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return respuesta





def importar_codigos_salon(request):
    """Carga CSV solo en categoria Salon (no aparece en el menu publico)."""
    if not request.session.get('dashboard_auth'):
        return redirect('pedidos:login_dashboard')
    if request.method != 'POST':
        return redirect(reverse('pedidos:panel_control') + '?tab=config#sm-herramientas-central')
    archivo = request.FILES.get('catalogo_salon_csv')
    if not archivo:
        messages.error(request, 'Seleccioná el CSV de los códigos del salón.')
        return redirect(reverse('pedidos:panel_control') + '?tab=config#sm-herramientas-central')
    try:
        filas = leer_catalogo_salon(archivo.read())
        resultado = importar_catalogo_salon(filas)
        messages.success(request,
            f"Salón: {resultado['creados']} productos importados, "
            f"{resultado['existentes']} ya existentes (sin cambios) y "
            f"{resultado['inactivos']} inactivos omitidos. No se agregó nada al menú público."
        )
    except (ErrorCatalogoSalon, ValueError) as exc:
        messages.error(request, f'No se importó el CSV: {exc}')
    return redirect(reverse('pedidos:panel_control') + '?tab=config#sm-herramientas-central')





# ---------------------------------------------------------------------------
# San Martin v111: editor rápido de productos EXCLUSIVOS del salón.
# No puede modificar productos del menú web.
# ---------------------------------------------------------------------------
@never_cache
def catalogo_salon_api(request):
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status': 'error', 'mensaje': 'Sesión vencida.'}, status=403)
    if request.method != 'GET':
        return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido.'}, status=405)
    if not obtener_configuracion().salon_habilitado:
        return JsonResponse({'status': 'error', 'mensaje': 'El salón está desactivado.'}, status=403)

    articulos = list(
        Producto.objects.filter(categoria__nombre='Salon')
        .values('id', 'codigo_rapido', 'nombre', 'precio', 'disponible')
    )
    articulos.sort(key=lambda a: (
        0 if str(a['codigo_rapido'] or '').isdigit() else 1,
        int(a['codigo_rapido']) if str(a['codigo_rapido'] or '').isdigit() else 0,
        str(a['codigo_rapido'] or ''),
        str(a['nombre']).casefold(),
        a['id'],
    ))
    return JsonResponse({
        'status': 'ok',
        'productos': [
            {
                'id': a['id'],
                'codigo': a['codigo_rapido'] or str(a['id']),
                'nombre': a['nombre'],
                'precio': str(a['precio']),
                'disponible': a['disponible'],
            }
            for a in articulos
        ],
    })




def editar_producto_salon(request, producto_id):
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status': 'error', 'mensaje': 'Sesión vencida.'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido.'}, status=405)
    if not obtener_configuracion().salon_habilitado:
        return JsonResponse({'status': 'error', 'mensaje': 'El salón está desactivado.'}, status=403)

    try:
        datos = json.loads(request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'status': 'error', 'mensaje': 'Solicitud inválida.'}, status=400)
    if not isinstance(datos, dict):
        return JsonResponse({'status': 'error', 'mensaje': 'Solicitud inválida.'}, status=400)

    codigo = str(datos.get('codigo') or '').strip()
    nombre = str(datos.get('nombre') or '').strip()
    texto_precio = str(datos.get('precio') or '').strip().replace(' ', '')
    disponible = datos.get('disponible')

    if not codigo.isascii() or not codigo.isdecimal() or not (1 <= len(codigo) <= 20) or int(codigo) <= 0:
        return JsonResponse({'status': 'error', 'mensaje': 'El código debe ser un número positivo (máximo 20 dígitos).'}, status=400)
    if not nombre or len(nombre) > 200:
        return JsonResponse({'status': 'error', 'mensaje': 'Ingresá un nombre de hasta 200 caracteres.'}, status=400)
    if not isinstance(disponible, bool):
        return JsonResponse({'status': 'error', 'mensaje': 'El estado del producto no es válido.'}, status=400)

    # Admite 3500, 3500.50, 3500,50 o 3.500,50.
    if ',' in texto_precio:
        texto_precio = texto_precio.replace('.', '').replace(',', '.')
    elif re.fullmatch(r'\d{1,3}(?:\.\d{3})+', texto_precio):
        # Precio argentino con separador de miles: 3.500 => 3500.
        texto_precio = texto_precio.replace('.', '')
    try:
        precio = Decimal(texto_precio)
    except (InvalidOperation, ValueError):
        return JsonResponse({'status': 'error', 'mensaje': 'Ingresá un precio válido.'}, status=400)
    if not precio.is_finite() or precio < 0 or precio > Decimal('99999999.99'):
        return JsonResponse({'status': 'error', 'mensaje': 'El precio debe estar entre $0 y $99.999.999,99.'}, status=400)
    if precio.as_tuple().exponent < -2:
        return JsonResponse({'status': 'error', 'mensaje': 'El precio admite hasta dos decimales.'}, status=400)

    with transaction.atomic():
        # El filtro por categoría protege el menú público incluso con un ID manipulado.
        producto = (
            Producto.objects.select_for_update()
            .filter(pk=producto_id, categoria__nombre='Salon')
            .first()
        )
        if not producto:
            return JsonResponse({'status': 'error', 'mensaje': 'Producto del salón no encontrado.'}, status=404)

        existe = Producto.objects.filter(
            categoria__nombre='Salon', codigo_rapido=codigo,
        ).exclude(pk=producto.pk).exists()
        if existe:
            return JsonResponse({
                'status': 'error', 'mensaje': f'El código {codigo} ya lo utiliza otro producto del salón.'
            }, status=409)

        producto.codigo_rapido = codigo
        producto.nombre = nombre
        producto.precio = precio
        producto.disponible = disponible
        producto.save(update_fields=['codigo_rapido', 'nombre', 'precio', 'disponible'])

    return JsonResponse({
        'status': 'ok',
        'mensaje': f'{nombre}: cambios guardados.',
        'producto': {
            'id': producto.id,
            'codigo': codigo,
            'nombre': nombre,
            'precio': str(precio),
            'disponible': disponible,
            'es_salon': True,
        },
    })





def salon(request):
    if not request.session.get('dashboard_auth'):
        return redirect(reverse('pedidos:login_dashboard') + '?next=' + reverse('pedidos:salon'))
    if not obtener_configuracion().salon_habilitado:
        messages.warning(request, 'El módulo Salón / Mesas está desactivado desde Configuración.')
        return redirect('pedidos:panel_control')
    productos_bd = Producto.objects.filter(disponible=True).select_related('categoria').order_by('categoria__nombre', 'orden', 'nombre')
    productos_js = [{'id': producto.id, 'codigo': producto.codigo_rapido if producto.codigo_rapido else str(producto.id), 'nombre': producto.nombre, 'precio': float(producto.precio), 'es_salon': producto.categoria.nombre == 'Salon'} for producto in productos_bd]
    mozos_js = [{'id': mozo.id, 'nombre': mozo.nombre} for mozo in Mozo.objects.all().order_by('nombre')]
    cuentas_credito_js = [
        {
            'id': cuenta.id,
            'nombre': cuenta.nombre,
            'telefono': cuenta.telefono,
            'saldo': float(cuenta.saldo_pos or Decimal('0.00')),
        }
        for cuenta in CuentaCorriente.objects.filter(activa=True)
            .annotate(saldo_pos=Sum('movimientos__monto'))
            .order_by('nombre', 'id')
    ]
    return render(request, 'pedidos/salon.html', {
        'mesas': range(1,101), 'productos': productos_js,
        'mozos': mozos_js, 'pedidos_web_salon': _salon_items_pedidos_web(),
        'cuentas_corrientes_pos': cuentas_credito_js,
        'fiscal_emision_activa': os.environ.get('ARCA_FISCAL_ENABLED')=='1' and (os.environ.get('ARCA_ENV','homologacion')!='produccion' or os.environ.get('ARCA_PRODUCCION_CONFIRMADA')=='SI'),
    })




# ===========================================================================
# COBRO REAL DE MESAS - ENTRA AL CIERRE DE CAJA
# ===========================================================================


# Endpoint de consulta SOLO LECTURA para resolver cobros sin respuesta del navegador.
# La confirmacion se guarda en la misma transaccion que los pedidos y las ventas.
@never_cache
def estado_cobro_salon(request):
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status': 'error', 'mensaje': 'No autorizado'}, status=403)
    if not obtener_configuracion().salon_habilitado:
        return JsonResponse({'status': 'error', 'mensaje': 'Salón desactivado'}, status=403)
    if request.method != 'GET':
        return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=405)
    operacion_id = str(request.GET.get('operacion_id') or '').strip()
    if not re.fullmatch(r'[a-zA-Z0-9_-]{12,64}', operacion_id):
        return JsonResponse({'status': 'error', 'mensaje': 'Identificador inválido'}, status=400)
    operacion = (OperacionCobroSalon.objects.filter(operacion_id=operacion_id)
                 .values('respuesta').first())
    if operacion and operacion['respuesta'] and operacion['respuesta'].get('status') == 'ok':
        return JsonResponse({'status': 'ok', 'confirmado': True,
                             'cobro': {**operacion['respuesta'], 'reintento': True}})
    # No encontrado y aun sin completar se reportan igual: nunca inferir que
    # el cobro NO ocurrio por una simple ausencia temporal en esta consulta.
    return JsonResponse({'status': 'ok', 'confirmado': False})


def cobrar_mesa_salon(request):
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status':'error','mensaje':'No autorizado'}, status=403)
    if not obtener_configuracion().salon_habilitado:
        return JsonResponse({'status':'error','mensaje':'Salón desactivado'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'status':'error','mensaje':'Método no permitido'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
        mesa = str(data.get('mesa','')).strip()
        medio = str(data.get('tipo_pago','')).lower().strip()
        mozo = str(data.get('mozo','')).strip()[:100]
        fiscal = bool(data.get('modo_fiscal'))
        if fiscal:
            # No aceptamos falsas facturas fiscales en el cobro normal.
            return JsonResponse({'status':'error', 'mensaje':
                'La emisión fiscal todavía está en preparación. La mesa sigue abierta. '                 'Usá * o ** para guardar un borrador NO fiscal.'}, status=409)
        items = data.get('items', [])
        if not mesa.isdigit() or not (1 <= int(mesa) <= 100):
            raise ValueError('Mesa inválida.')
        mesa = str(int(mesa))
        if medio not in ('efectivo', 'mercadopago', 'debito', 'cuenta_corriente'):
            raise ValueError('Elegí un medio de pago válido.')
        if not isinstance(items, list) or not items:
            raise ValueError('No hay productos para cobrar.')
        es_cuenta_corriente = medio == 'cuenta_corriente'
        cuenta_credito_id = None
        operacion_id = str(data.get('operacion_id') or '').strip()
        # Los nuevos clientes envían UUID para todos los medios de pago.
        # Compatibilidad: clientes antiguos sin UUID pueden seguir cobrando,
        # aunque no contarán con protección contra reintentos.
        if operacion_id and not re.fullmatch(r'[a-zA-Z0-9_-]{12,64}', operacion_id):
            raise ValueError('El identificador del cobro no es válido.')
        if es_cuenta_corriente:
            if fiscal:
                raise ValueError('El cierre fiscal no puede registrarse como cuenta corriente.')
            try:
                cuenta_credito_id = int(data.get('cuenta_corriente_id') or 0)
            except (TypeError, ValueError):
                raise ValueError('Elegí una persona para cargar la cuenta corriente.')
            if cuenta_credito_id <= 0 or not re.fullmatch(r'[a-zA-Z0-9_-]{12,64}', operacion_id):
                raise ValueError('Falta cliente o identificador de cobro válido.')
    except (ValueError, UnicodeDecodeError, TypeError) as exc:
        return JsonResponse({'status':'error','mensaje':str(exc)}, status=400)

    try:
        with transaction.atomic():
            cuenta_credito = None
            saldo_credito = None
            if es_cuenta_corriente:
                # En un reintento de red no volvemos a cobrar una deuda ya registrada.
                movimiento_previo = MovimientoCuentaCorriente.objects.filter(
                    operacion_id=operacion_id,
                ).select_related('cuenta').first()
                if movimiento_previo:
                    if movimiento_previo.cuenta_id != cuenta_credito_id:
                        raise ValueError('El identificador de cobro corresponde a otra cuenta.')
                    return JsonResponse({
                        'status': 'ok', 'reintento': True,
                        'tipo_pago': 'cuenta_corriente',
                        'cuenta_corriente_id': movimiento_previo.cuenta_id,
                        'cuenta_corriente_nombre': movimiento_previo.cuenta.nombre,
                        'cuenta_saldo': float(movimiento_previo.cuenta.saldo_actual),
                        'total': float(-movimiento_previo.monto),
                        'mensaje': 'El consumo ya estaba cargado en la cuenta corriente.',
                        'comprobante_id': (movimiento_previo.comprobante_pos.pk if hasattr(movimiento_previo, 'comprobante_pos') else None),
                    })
                cuenta_credito = CuentaCorriente.objects.select_for_update().filter(
                    pk=cuenta_credito_id, activa=True,
                ).first()
                if not cuenta_credito:
                    raise ValueError('La cuenta corriente no existe o está desactivada.')
            operacion_cobro = None
            if operacion_id:
                # El hash impide reutilizar un mismo identificador con otra mesa
                # u otros productos, incluso después de una reconexión.
                firma_payload = hashlib.sha256(json.dumps({
                    'mesa': mesa, 'tipo_pago': medio, 'mozo': mozo,
                    'cuenta_corriente_id': cuenta_credito_id, 'items': items,
                }, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
                operacion_cobro, creada = OperacionCobroSalon.objects.get_or_create(
                    operacion_id=operacion_id, defaults={
                        'mesa': mesa, 'tipo_pago': medio, 'firma': firma_payload,
                    })
                if not creada:
                    if operacion_cobro.firma != firma_payload:
                        raise ValueError('Este identificador de cobro pertenece a otra operación. Recargá el salón antes de reintentar.')
                    if operacion_cobro.respuesta:
                        return JsonResponse({**operacion_cobro.respuesta, 'reintento': True})
                    return JsonResponse({'status': 'error', 'mensaje':
                        'El cobro está en proceso. Consultá Ventas antes de volver a intentarlo.'}, status=409)
            filas_pos = []
            snapshot_items = []
            web_solicitados = {}
            for fila in items:
                if not isinstance(fila,dict):
                    raise ValueError('Hay productos inválidos.')
                detalle_id = fila.get('detalle_id')
                if detalle_id:
                    try:
                        did = int(detalle_id)
                        pedido_id = int(fila.get('pedido_id') or 0)
                        cantidad = int(fila.get('cantidad') or 0)
                    except (TypeError, ValueError):
                        raise ValueError('Datos de pedido web inválidos.')
                    if did <= 0 or pedido_id <= 0 or cantidad <= 0 or did in web_solicitados:
                        raise ValueError('Pedido web repetido o cantidad inválida.')
                    web_solicitados[did] = (pedido_id, cantidad)
                else:
                    filas_pos.append(fila)

            web_por_pedido = {}
            pedidos_web_bloqueados = {}
            if web_solicitados:
                # Bloquea primero la orden completa para evitar dobles cobros concurrentes.
                ids_pedidos = {pid for pid, cant in web_solicitados.values()}
                pedidos_web_bloqueados = {
                    p.pk: p for p in Pedido.objects.select_for_update()
                    .filter(pk__in=ids_pedidos).order_by('pk')
                }
                detalles = (DetallePedido.objects.select_for_update()
                    .select_related('producto')
                    .filter(pk__in=web_solicitados.keys())
                    .order_by('pedido_id','pk'))
                if detalles.count() != len(web_solicitados):
                    raise ValueError('Un producto web ya no está disponible. Actualizá el salón.')
                for d in detalles:
                    pid, cant = web_solicitados[d.pk]
                    pedido = pedidos_web_bloqueados.get(d.pedido_id)
                    if pedido is None:
                        raise ValueError('El pedido web ya no está disponible.')
                    numero = str(pedido.numero_mesa or '').strip()
                    if (pid != pedido.pk or not numero.isdigit() or str(int(numero)) != mesa
                        or pedido.tipo_entrega != 'mesa' or pedido.tipo_pago != 'efectivo'
                        or pedido.estado in ('cancelado','entregado')
                        or (pedido.nombre_cliente or '').upper().startswith('POS SALON')
                        or cant > d.cantidad):
                        raise ValueError('El pedido web fue modificado o ya se cobró. Actualizá el salón.')
                    web_por_pedido.setdefault(pid,[]).append((d,cant))

            total_cobrado = Decimal('0.00')
            cerrados = []
            pedido_pos = None
            if filas_pos:
                pedido_pos = Pedido.objects.create(
                    estado='listo', total=Decimal('0.00'),
                    nombre_cliente='POS SALON FISCAL' if fiscal else 'POS SALON',
                    tipo_entrega='mesa', numero_mesa=mesa, mozo=mozo,
                    tipo_pago=medio, punto_venta=None, impreso_caja=True,  # v150: Pagar no reimprime el control
                )
                subtotal=Decimal('0.00')
                for item in filas_pos:
                    try:
                        producto_id = int(item.get('producto_id') or 0)
                        codigo = str(item.get('codigo') or '').strip()
                        cantidad = int(item.get('cantidad') or 0)
                        precio = Decimal(str(item.get('precio')))
                    except (TypeError, ValueError, InvalidOperation):
                        raise ValueError('Precio o cantidad inválida.')
                    producto = Producto.objects.filter(pk=producto_id).first() if producto_id else None
                    # Productos persistidos en el navegador pueden venir de
                    # una versión vieja del catálogo. Antes de cobrar, validamos
                    # el código y evitamos asociarlos a un producto equivocado.
                    if producto and producto.codigo_rapido and codigo and str(producto.codigo_rapido) != codigo:
                        producto = None
                    if producto is None and codigo:
                        candidatos = list(Producto.objects.filter(codigo_rapido=codigo)[:2])
                        if len(candidatos) > 1:
                            raise ValueError(f'El código {codigo} está duplicado en el catálogo. Revisalo antes de cobrar.')
                        if candidatos:
                            producto = candidatos[0]
                    if producto is None and codigo.isdigit() and not producto_id:
                        producto = Producto.objects.filter(pk=int(codigo)).first()
                    if not producto or cantidad <= 0 or precio < 0:
                        nombre = str(item.get('nombre') or codigo or 'sin nombre')[:70]
                        raise ValueError(f'No se pudo identificar "{nombre}" en el catálogo actual. La mesa sigue abierta; actualizá el producto antes de cobrar.')
                    DetallePedido.objects.create(pedido=pedido_pos, producto=producto,
                        cantidad=cantidad, precio_unitario=precio)
                    snapshot_items.append({
                        'cantidad': cantidad, 'nombre': producto.nombre,
                        'unitario': str(precio), 'subtotal': str(precio*cantidad),
                    })
                    subtotal += precio*cantidad
                pedido_pos.total=subtotal
                pedido_pos.save(update_fields=['total'])
                total_cobrado += subtotal
                if fiscal:
                    cache.set(f'fiscal_{pedido_pos.pk}',True,timeout=300)

            for pid, tomados in web_por_pedido.items():
                pedido_web = pedidos_web_bloqueados[pid]
                all_details = list(DetallePedido.objects.filter(pedido_id=pid).order_by('pk'))
                cantidades = {d.pk: cant for d,cant in tomados}
                es_total = all(d.pk in cantidades and cantidades[d.pk]==d.cantidad for d in all_details)
                subtotal_web = sum((d.precio_unitario*cant for d,cant in tomados),Decimal('0.00'))
                for d, cant in tomados:
                    nombre_detalle = d.producto.nombre if d.producto else 'Producto eliminado'
                    opciones = [str(getattr(d, campo, '') or '') for campo in (
                        'variante_elegida', 'guarnicion_elegida', 'punto_coccion_elegido',
                        'relleno_elegido', 'salsa_elegida', 'adicional_elegido', 'hielo_elegido',
                    )]
                    detalle_extra = ', '.join(opcion for opcion in opciones if opcion)
                    snapshot_items.append({
                        'cantidad': cant,
                        'nombre': nombre_detalle + (f' ({detalle_extra})' if detalle_extra else ''),
                        'unitario': str(d.precio_unitario),
                        'subtotal': str(d.precio_unitario * cant),
                    })
                if es_total:
                    pedido_web.estado='entregado'
                    pedido_web.tipo_pago=medio
                    pedido_web.mozo=mozo
                    if es_cuenta_corriente:
                        pedido_web.impreso_caja = True
                    pedido_web.save(update_fields=['estado','tipo_pago','mozo','impreso_caja'] if es_cuenta_corriente else ['estado','tipo_pago','mozo'])
                    cerrados.append(pid)
                    if fiscal:
                        cache.set(f'fiscal_{pid}',True,timeout=300)
                else:
                    # Mantener la parte aún no cobrada en el pedido original.
                    pagado=Pedido.objects.create(
                        estado='entregado', total=subtotal_web, nombre_cliente='POS SALON PARCIAL',
                        tipo_entrega='mesa', numero_mesa=mesa, mozo=mozo,
                        tipo_pago=medio, punto_venta=pedido_web.punto_venta,
                        impreso_caja=True,  # v150: un cobro parcial no vuelve a imprimir
                    )
                    for detalle,cant in tomados:
                        DetallePedido.objects.create(
                            pedido=pagado,producto=detalle.producto,
                            cantidad=cant,precio_unitario=detalle.precio_unitario,
                            variante_elegida=detalle.variante_elegida,
                            guarnicion_elegida=detalle.guarnicion_elegida,
                            punto_coccion_elegido=detalle.punto_coccion_elegido,
                            relleno_elegido=detalle.relleno_elegido,
                            salsa_elegida=detalle.salsa_elegida,
                            adicional_elegido=detalle.adicional_elegido,
                            hielo_elegido=detalle.hielo_elegido,
                        )
                        if cant == detalle.cantidad:
                            detalle.delete()
                        else:
                            detalle.cantidad -= cant
                            detalle.save(update_fields=['cantidad'])
                    pedido_web.total = sum((d.precio_unitario*d.cantidad for d in pedido_web.items.all()),Decimal('0.00'))
                    pedido_web.save(update_fields=['total'])
                    cerrados.append(pagado.pk)
                    if fiscal:
                        cache.set(f'fiscal_{pagado.pk}',True,timeout=300)
                total_cobrado += subtotal_web

            if not filas_pos and not web_por_pedido:
                raise ValueError('No hay productos para cobrar.')

            if es_cuenta_corriente:
                if total_cobrado <= 0:
                    raise ValueError('El consumo debe tener un importe mayor a cero.')
                saldo_anterior = CuentaCorriente.objects.filter(pk=cuenta_credito.pk).aggregate(
                    saldo=Sum('movimientos__monto'),
                )['saldo'] or Decimal('0.00')
                movimiento_credito = MovimientoCuentaCorriente.objects.create(
                    cuenta=cuenta_credito,
                    tipo='consumo',
                    descripcion=f'Consumo Salón POS · Mesa {mesa}',
                    monto=-total_cobrado,
                    operacion_id=operacion_id,
                )
                saldo_credito = saldo_anterior - total_cobrado
                comprobante_credito = ComprobanteCuentaCorriente.objects.create(
                    cuenta=cuenta_credito, movimiento=movimiento_credito,
                    tipo='consumo', cliente_nombre=cuenta_credito.nombre,
                    mesa=mesa, mozo=mozo, items=snapshot_items,
                    total=total_cobrado, saldo_anterior=saldo_anterior,
                    saldo_posterior=saldo_credito,
                )

            respuesta = {
                'status': 'ok',
                'pedido_id': pedido_pos.pk if pedido_pos else (cerrados[0] if cerrados else None),
                'pedidos_web_cerrados': cerrados,
                'total': float(total_cobrado),
                'tipo_pago': medio,
                'modo_fiscal': fiscal,
                'mensaje': 'Consumo cargado en cuenta corriente.' if es_cuenta_corriente else 'Cobro registrado y mesa actualizada.',
            }
            if es_cuenta_corriente:
                respuesta.update({
                    'cuenta_corriente_id': cuenta_credito.pk,
                    'cuenta_corriente_nombre': cuenta_credito.nombre,
                    'cuenta_saldo': float(saldo_credito),
                    'comprobante_id': comprobante_credito.pk,
                })
            if operacion_cobro is not None:
                operacion_cobro.respuesta = respuesta
                operacion_cobro.save(update_fields=['respuesta'])

    except ValueError as exc:
        return JsonResponse({'status':'error','mensaje':str(exc)},status=400)
    except Exception:
        ref_error = uuid.uuid4().hex[:8].upper()
        logging.getLogger(__name__).exception('Error al cerrar mesa POS ref=%s', ref_error)
        return JsonResponse({'status':'error','mensaje':
            'No se pudo cerrar la mesa. No borres sus productos. Revisá Render Logs con el código ' + ref_error,
            'error_ref': ref_error}, status=500)
    return JsonResponse(respuesta)






# ===========================================================================
# STERAKFOOD V105 - COMPROBANTES DE DEUDA NO FISCALES
# ===========================================================================

def _token_ticketera_valido(request):
    # Si se configura en Render y en la PC, protege datos personales del ticket.
    token = os.environ.get('TICKETERA_PRINT_TOKEN', '').strip()
    if not token:
        return False  # el token es obligatorio para leer datos personales de la cola
    recibido = request.headers.get('X-Ticketera-Token', '')
    return secrets.compare_digest(token, recibido)


def _resumen_ticket_comprobante(comprobante, id_cola):
    return {
        'id': id_cola,
        'comprobante_id': comprobante.pk,
        'tipo': comprobante.tipo,
        'cliente': comprobante.cliente_nombre,
        'mesa': comprobante.mesa,
        'mozo': comprobante.mozo,
        'fecha': localtime(comprobante.fecha).strftime('%d/%m/%Y %H:%M'),
        'items': comprobante.items,
        'total': str(comprobante.total),
        'saldo_anterior': str(comprobante.saldo_anterior),
        'saldo_posterior': str(comprobante.saldo_posterior),
    }


def imprimir_comprobante_cuenta(request, comprobante_id):
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status': 'error', 'mensaje': 'Sesión vencida.'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido.'}, status=405)
    comprobante = get_object_or_404(ComprobanteCuentaCorriente, pk=comprobante_id)
    trabajo = ImpresionComprobanteCuenta.objects.create(comprobante=comprobante)
    return JsonResponse({
        'status': 'ok', 'cola_id': trabajo.pk,
        'mensaje': 'Comprobante enviado a la cola de la ticketera de caja.',
    })


def imprimir_estado_cuenta(request, cuenta_id):
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status': 'error', 'mensaje': 'Sesión vencida.'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido.'}, status=405)
    cuenta = get_object_or_404(CuentaCorriente, pk=cuenta_id)
    with transaction.atomic():
        saldo = CuentaCorriente.objects.filter(pk=cuenta_id).aggregate(
            saldo=Sum('movimientos__monto')
        )['saldo'] or Decimal('0.00')
        ultimos = list(cuenta.movimientos.order_by('-fecha', '-pk')[:8])
        items = [{
            'cantidad': 1,
            'nombre': m.descripcion or m.get_tipo_display(),
            'unitario': str(m.monto), 'subtotal': str(m.monto),
        } for m in reversed(ultimos)]
        comprobante = ComprobanteCuentaCorriente.objects.create(
            cuenta=cuenta, tipo='estado', cliente_nombre=cuenta.nombre,
            items=items, total=Decimal('0.00'),
            saldo_anterior=saldo, saldo_posterior=saldo,
        )
        trabajo = ImpresionComprobanteCuenta.objects.create(comprobante=comprobante)
    return JsonResponse({
        'status': 'ok', 'cola_id': trabajo.pk,
        'mensaje': 'Estado de cuenta enviado a la ticketera.',
    })


def api_tickets_cuenta_pendientes(request):
    if not _token_ticketera_valido(request):
        return JsonResponse({'status': 'error', 'mensaje': 'Token de ticketera inválido'}, status=403)
    pendientes = (ImpresionComprobanteCuenta.objects
        .filter(impreso=False)
        .select_related('comprobante')
        .order_by('pk')[:30])
    return JsonResponse({'status': 'ok', 'tickets': [
        _resumen_ticket_comprobante(job.comprobante, job.pk)
        for job in pendientes
    ]})


@csrf_exempt
def api_ticket_cuenta_impreso(request, trabajo_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=405)
    if not _token_ticketera_valido(request):
        return JsonResponse({'status': 'error', 'mensaje': 'Token de ticketera inválido'}, status=403)
    actualizado = (ImpresionComprobanteCuenta.objects
        .filter(pk=trabajo_id, impreso=False)
        .update(impreso=True, fecha_impreso=timezone.now()))
    return JsonResponse({'status': 'ok' if actualizado else 'error'})


# Componentes de Salon POS restaurados de la version pre-offline.
# pedidos_del_panel
def pedidos_del_panel():
    """Pedidos web/mostrador. Las operaciones del POS no son pedidos online.

    El POS registra sus cobros en Pedido para conservar las ventas y el cierre de
    caja. Ocultarlos del panel NO debe borrarlos ni excluirlos de esos reportes.
    Se usan las marcas ya existentes, sin migrar ni modificar datos historicos.
    """
    return (
        Pedido.objects
        .filter(archivado_ventas=False)
        .exclude(tipo_pago='ticket_salon_temporal')
        .exclude(tipo_entrega='mesa', nombre_cliente__istartswith='POS SALON')
    )



# _es_ajax_cuentas
def _es_ajax_cuentas(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'



# _acceso_cuentas
def _acceso_cuentas(request):
    if request.session.get('dashboard_auth'):
        return None
    if _es_ajax_cuentas(request):
        return JsonResponse({'status': 'error', 'mensaje': 'La sesión venció. Iniciá sesión nuevamente.'}, status=403)
    return redirect('pedidos:login_dashboard')



# _error_cuentas
def _error_cuentas(request, mensaje, cuenta_id=None):
    if _es_ajax_cuentas(request):
        return JsonResponse({'status': 'error', 'mensaje': mensaje}, status=400)
    messages.error(request, mensaje)
    return _redirect_tab_cuentas(cuenta_id)



# _ok_cuentas
def _ok_cuentas(request, mensaje, cuenta_id=None, eliminado=False):
    if not _es_ajax_cuentas(request):
        messages.success(request, mensaje)
        return _redirect_tab_cuentas(None if eliminado else cuenta_id)
    cuentas, total_deuda, total_favor = _preparar_cuentas_corrientes()
    cuenta = next((c for c in cuentas if c.pk == cuenta_id), None) if not eliminado else None
    return JsonResponse({
        'status': 'ok',
        'mensaje': mensaje,
        'cuenta_id': cuenta_id,
        'eliminada': eliminado,
        'html': render_to_string('pedidos/_cuenta_tarjeta.html', {'cuenta': cuenta}, request=request) if cuenta else '',
        'total_deuda': str(total_deuda),
        'total_favor': str(total_favor),
        'total_cuentas': len(cuentas),
    })



# saldar_cuenta_corriente
def saldar_cuenta_corriente(request, cuenta_id):
    """Registra el pago exacto del saldo deudor; no elimina el historial.

    La operación afecta solo a la cuenta corriente. No crea una venta ni un
    movimiento de caja, porque estos cobros todavía no comparten una caja única.
    """
    sin_acceso = _acceso_cuentas(request)
    if sin_acceso is not None:
        return sin_acceso
    if request.method != 'POST':
        return _error_cuentas(request, 'Usá el botón Saldar deuda.', cuenta_id)

    with transaction.atomic():
        cuenta = get_object_or_404(CuentaCorriente.objects.select_for_update(), pk=cuenta_id)
        saldo = (MovimientoCuentaCorriente.objects
                 .filter(cuenta=cuenta).aggregate(total=Sum('monto'))['total'] or Decimal('0.00'))
        if saldo >= 0:
            return _error_cuentas(request, 'Esta cuenta ya está al día o tiene saldo a favor.', cuenta_id)
        monto = -saldo
        MovimientoCuentaCorriente.objects.create(
            cuenta=cuenta, tipo='pago', monto=monto,
            descripcion='Pago total de deuda registrado desde Cuentas',
        )
    importe = f'{monto:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return _ok_cuentas(request, f'Deuda de {cuenta.nombre} saldada por ${importe}.', cuenta.id)



# reiniciar_historial_ventas
def reiniciar_historial_ventas(request):
    """Archive completed sales in reports, without deleting any financial records.

    NEVER touches CuentaCorriente, MovimientoCuentaCorriente, their comprobantes,
    active web orders or print statuses. Does not erase fiscal documents or CAE.
    """
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status': 'error', 'mensaje': 'No autorizado'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'mensaje': 'Se requiere POST'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'status': 'error', 'mensaje': 'Datos inválidos'}, status=400)
    if data.get('confirmacion') != 'REINICIAR':
        return JsonResponse({'status': 'error', 'mensaje': 'Escribí REINICIAR para confirmar'}, status=400)

    # Only completed and cancelled orders get hidden from current history.
    # Pending/in-preparation web orders remain available to kitchen and staff.
    with transaction.atomic():
        candidatos = (Pedido.objects.select_for_update()
                      .filter(archivado_ventas=False,
                              estado__in=['listo', 'entregado', 'cancelado'])
                      .exclude(tipo_pago__in=['ticket_salon_temporal', 'pendiente_para_llevar']))
        # Lock and enumerate completed records to keep amount/count consistent.
        # No aggregate over SELECT FOR UPDATE (PostgreSQL disallows that combination).
        cantidad = 0
        total = Decimal('0.00')
        for estado, monto in candidatos.values_list('estado', 'total').iterator(chunk_size=500):
            cantidad += 1
            if estado != 'cancelado':
                total += monto or Decimal('0.00')
        # Keep even empty reset events to provide a reliable audit trail.
        corte = CorteHistorialVentas.objects.create(
            cantidad_pedidos=cantidad, total_archivado=total,
            origen='salon_o_panel')
        candidatos.update(archivado_ventas=True, corte_ventas=corte)

    return JsonResponse({
        'status': 'ok',
        'mensaje': 'Se reinició el historial visible de ventas. Los originales y cuentas corrientes siguen guardados.',
        'corte_id': corte.pk,
        'cantidad_archivada': cantidad,
        'total_archivado': str(total),
    })



# salon_resumen_ventas_api
def salon_resumen_ventas_api(request):
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status': 'error', 'mensaje': 'No autorizado'}, status=403)
    if request.method != 'GET':
        return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=405)
    hoy = timezone.localdate()
    # Los tickets de control no son ventas. Solo pedidos finalizados del día.
    # Un pedido de cliente aún en preparación no se toma como cobrado.
    pedidos = (Pedido.objects.filter(fecha_creacion__date=hoy, archivado_ventas=False)
               .filter(Q(estado__in=['listo', 'entregado']) |
                       Q(tipo_entrega='para_llevar', tipo_pago__in=['efectivo', 'debito', 'mercadopago']))
               .exclude(tipo_pago__in=['ticket_salon_temporal', 'pendiente_para_llevar']))
    total = pedidos.aggregate(importe=Sum('total'))['importe'] or Decimal('0.00')
    salon = (pedidos.filter(tipo_entrega='mesa')
             .aggregate(importe=Sum('total'))['importe'] or Decimal('0.00'))
    from .models import FacturaFiscal
    # Se muestra por separado: todavía NO se puede conciliar automáticamente
    # factura contra cada cobro, porque las mesas actuales se guardan en navegador.
    autorizadas = FacturaFiscal.objects.filter(creado__date=hoy, estado='autorizada')
    importe_fiscal = autorizadas.aggregate(importe=Sum('total'))['importe'] or Decimal('0.00')
    return JsonResponse({
        'status': 'ok',
        'fecha': hoy.isoformat(),
        'total_registrado': float(total),
        'total_salon': float(salon),
        'total_para_llevar': float(pedidos.filter(tipo_entrega='para_llevar').aggregate(importe=Sum('total'))['importe'] or Decimal('0.00')),
        'total_facturado_fiscal': float(importe_fiscal),
        'cantidad_facturas_fiscales': autorizadas.count(),
        'facturacion_fiscal_disponible': os.environ.get('ARCA_FISCAL_ENABLED')=='1',
        'nota_fiscal': 'Facturas con CAE emitidas hoy. NO equivale a conciliación con cada cobro; consultá el historial fiscal.',
    })



# _cuit_valido
def _cuit_valido(cuit):
    if not re.fullmatch(r'\d{11}', cuit):
        return False
    pesos = (5,4,3,2,7,6,5,4,3,2)
    resto = 11 - (sum(int(n) * peso for n, peso in zip(cuit[:10], pesos)) % 11)
    return (0 if resto == 11 else 9 if resto == 10 else resto) == int(cuit[10])



# fiscal_preparacion
def fiscal_preparacion(request):
    if not request.session.get('dashboard_auth'):
        return redirect('pedidos:login_dashboard')
    config, _ = ConfiguracionFiscal.objects.get_or_create(pk=1)
    if request.method == 'POST':
        razon = (request.POST.get('razon_social') or '').strip()[:180]
        cuit = (request.POST.get('cuit') or '').replace('-', '').replace(' ', '')
        condicion = (request.POST.get('condicion_iva') or '').strip()
        domicilio = (request.POST.get('domicilio_fiscal') or '').strip()[:220]
        pv = (request.POST.get('punto_venta_referencia') or '').strip()
        if cuit and not _cuit_valido(cuit):
            messages.error(request, 'El CUIT ingresado no pasa la validación de dígito verificador.')
        elif condicion not in dict(ConfiguracionFiscal.CONDICIONES_IVA):
            messages.error(request, 'Condición de IVA inválida.')
        elif pv and (not pv.isdigit() or not (1 <= int(pv) <= 99999)):
            messages.error(request, 'El punto de venta de referencia debe ser un número entre 1 y 99999.')
        else:
            config.razon_social = razon
            config.cuit = cuit
            config.condicion_iva = condicion
            config.domicilio_fiscal = domicilio
            config.punto_venta_referencia = int(pv) if pv else None
            config.save()
            messages.success(request, 'Datos guardados. NO habilitan la facturación electrónica.')
            return redirect('pedidos:fiscal_preparacion')
    borradores = BorradorFiscal.objects.order_by('-fecha_creacion')[:30]
    return render(request, 'pedidos/fiscal_preparacion.html', {
        'config_fiscal': config,
        'condiciones_iva': ConfiguracionFiscal.CONDICIONES_IVA,
        'borradores_fiscales': borradores,
    })



# fiscal_guardar_borrador
def fiscal_guardar_borrador(request):
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status':'error','mensaje':'No autorizado.'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'status':'error','mensaje':'Método no permitido.'}, status=405)
    if not obtener_configuracion().salon_habilitado:
        return JsonResponse({'status':'error','mensaje':'El Salón está desactivado.'}, status=403)
    try:
        if len(request.body) > 100_000:
            raise ValueError('El borrador es demasiado grande.')
        data = json.loads(request.body.decode('utf-8'))
        identificador = UUID(str(data.get('operacion_id') or ''))
        mesa = str(data.get('mesa') or '').strip()
        if not mesa.isdigit() or not (1 <= int(mesa) <= 100):
            raise ValueError('Mesa inválida.')
        mesa = str(int(mesa))
        items = data.get('items')
        if not isinstance(items, list) or not 1 <= len(items) <= 150:
            raise ValueError('Ingresá entre 1 y 150 renglones de productos.')
        guardados = []
        total = Decimal('0.00')
        for item in items:
            if not isinstance(item, dict):
                raise ValueError('Renglón inválido.')
            cantidad = int(item.get('cantidad'))
            precio = Decimal(str(item.get('precio')))
            if (not 1 <= cantidad <= 1000 or not precio.is_finite()
                    or precio < 0 or precio > Decimal('9999999.99')
                    or precio != precio.quantize(Decimal('0.01'))):
                raise ValueError('Importe o cantidad fuera de rango.')
            codigo = str(item.get('codigo') or '')[:30]
            nombre = str(item.get('nombre') or '').strip()[:200]
            if not nombre or not (str(item.get('producto_id') or '').isdigit() or codigo):
                raise ValueError('Producto incompleto.')
            subtotal = precio * cantidad
            total += subtotal
            guardados.append({'producto_id': str(item.get('producto_id') or '')[:20],
                'codigo': codigo, 'nombre': nombre, 'cantidad': cantidad,
                'precio': str(precio), 'subtotal': str(subtotal),
                'pedido_id': str(item.get('pedido_id') or '')[:20],
                'detalle_id': str(item.get('detalle_id') or '')[:20]})
        if not Decimal('0.00') < total < Decimal('1000000000.00'):
            raise ValueError('Total estimado inválido.')
        mozo = str(data.get('mozo') or '')[:100]
        # La operación se identifica por UUID: reintentos no crean nuevos borradores.
        borrador, creado = BorradorFiscal.objects.get_or_create(
            operacion_id=identificador,
            defaults={'mesa': mesa,'mozo': mozo,'items': guardados,'total_estimado': total})
        if not creado and (borrador.mesa != mesa or borrador.items != guardados):
            raise ValueError('El identificador ya corresponde a otro borrador. Refrescá la mesa.')
    except (ValueError, TypeError, ArithmeticError, OverflowError, InvalidOperation, UnicodeDecodeError, json.JSONDecodeError) as error:
        return JsonResponse({'status':'error','mensaje':str(error)}, status=400)
    return JsonResponse({'status':'ok', 'borrador_id':borrador.pk,
        'mensaje':'Borrador guardado. NO es factura, NO tiene CAE y NO cerró la mesa.',
        'reintento':not creado})



# fiscal_probar_conexion_arca
def fiscal_probar_conexion_arca(request):
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status': 'error', 'mensaje': 'No autorizado.'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido.'}, status=405)
    from .arca_homologacion import ArcaDiagnosticoError, fedummy_homologacion
    try:
        resultado = fedummy_homologacion()
    except ArcaDiagnosticoError as exc:
        return JsonResponse({'status': 'error', 'mensaje': str(exc), 'entorno': 'HOMOLOGACION'}, status=502)
    return JsonResponse({'status': 'ok' if resultado['disponible'] else 'aviso',
                         'entorno': 'HOMOLOGACION',
                         'estados': resultado['estados'],
                         'mensaje': 'Prueba de conectividad completada. Sin autenticación y SIN facturas.',
                         'autenticado': False, 'comprobante_emitido': False})



# respaldo_mesas_local_api
def respaldo_mesas_local_api(request):
    if not getattr(settings, 'SM_LOCAL_MODE', False):
        raise Http404
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status': 'error', 'mensaje': 'No autorizado'}, status=403)
    if request.method not in ('GET', 'POST'):
        return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=405)
    if request.method == 'GET':
        registro = RespaldoMesasLocal.objects.filter(pk=1).first()
        return JsonResponse({'status': 'ok', 'version': registro.version if registro else 0,
                             'cuentas': registro.datos if registro else {}})
    if len(request.body) > 800_000:
        return JsonResponse({'status': 'error', 'mensaje': 'Respaldo excesivo'}, status=413)
    try:
        payload = json.loads(request.body)
        cuentas = payload['cuentas']
        version = payload['version']
        if not isinstance(cuentas, dict) or not isinstance(version, int) or isinstance(version,bool) or version < 0:
            raise ValueError()
        if len(cuentas) > 110 or any(
            not str(m).isdigit() or not 1 <= int(m) <= 100 or
            not isinstance(c, dict) or not isinstance(c.get('items', []), list) or
            len(c.get('items', [])) > 250
            for m, c in cuentas.items()
        ):
            raise ValueError()
    except (ValueError, KeyError, TypeError, UnicodeError):
        return JsonResponse({'status': 'error', 'mensaje': 'Estado de mesas inválido'}, status=400)
    # CAS: evita que otra pestaña sobrescriba silenciosamente consumos.
    # La fila se crea solo una vez; en SQLite las escrituras son transaccionales.
    try:
        with transaction.atomic():
            RespaldoMesasLocal.objects.get_or_create(pk=1)
            actualizados = RespaldoMesasLocal.objects.filter(pk=1, version=version).update(
                datos=cuentas, version=F('version') + 1, modificado=timezone.now()
            )
    except Exception:
        return JsonResponse({'status': 'error', 'mensaje': 'Base local ocupada, reintentá'}, status=503)
    if actualizados != 1:
        return JsonResponse({'status': 'conflicto', 'mensaje': 'Otra ventana actualizó las mesas. Recargá para evitar sobrescribir.',}, status=409)
    return JsonResponse({'status': 'ok', 'version': version+1})



# estado_ticket_salon
def estado_ticket_salon(request):
    """Estado de tickets temporales confirmados por la ticketera de Windows.

    Solo muestra tickets del salón; no devuelve datos de clientes ni ventas.
    """
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status': 'error', 'mensaje': 'No autorizado'}, status=403)
    if request.method != 'GET':
        return JsonResponse({'status': 'error', 'mensaje': 'Metodo no permitido'}, status=405)
    raw = str(request.GET.get('ids', ''))
    partes = raw.split(',')
    if len(partes) > 100 or any(not p.isdigit() for p in partes if p):
        return JsonResponse({'status': 'error', 'mensaje': 'IDs invalidos'}, status=400)
    ids = [int(p) for p in partes if p.isdigit() and 0 < int(p) < 2**63]
    filas = Pedido.objects.filter(pk__in=ids, tipo_pago='ticket_salon_temporal').values('id', 'impreso_caja')
    return JsonResponse({'status': 'ok', 'estados': {
        str(fila['id']): 'impreso' if fila['impreso_caja'] else 'pendiente' for fila in filas
    }})


