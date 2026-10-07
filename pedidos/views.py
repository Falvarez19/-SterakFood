import json
import re
import requests
import urllib.parse
import os
import tarfile
import mercadopago
from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.core.management import call_command
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, Http404
from django.contrib import messages
from django.contrib.staticfiles import finders
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import localtime
from django.utils import timezone
from django.core.cache import cache
from django.db import connection, transaction
from django.db.models import Q, Sum
from .forms import ProductoForm
from .models import Producto, Pedido, DetallePedido, PuntoVenta, Categoria, Configuracion, OpinionCliente, Mozo
from django.core.exceptions import PermissionDenied


# ==========================================================================
# MÓDULO 1: VISTAS DEL CLIENTE (MENÚ PÚBLICO)
# ==========================================================================


def obtener_configuracion():
    config, _ = Configuracion.objects.get_or_create(id=1)
    return config


def descuento_efectivo_vigente(config):
    # Si el switch "Descuento en efectivo" está prendido, el descuento se aplica.
    # Antes estaba limitado a sábado/domingo de 12 a 14 hs.
    return config.descuento_efectivo_activo


def cierre_automatico_en_curso(config):
    if not config.cierre_automatico_activo or not config.hora_cierre:
        return False
    return timezone.localtime(timezone.now()).time().replace(tzinfo=None) >= config.hora_cierre


def pedidos_online_habilitados(config):
    if cierre_automatico_en_curso(config):
        if config.buffet_habilitado:
            config.buffet_habilitado = False
            config.save(update_fields=['buffet_habilitado'])
        return False
    return config.buffet_habilitado


def bienvenida_disponible():
    return bool(finders.find('img/bienvenida_buffet.webp'))


def inicio(request):
    config = obtener_configuracion()
    buffet_habilitado = pedidos_online_habilitados(config)
    descuento_activo = descuento_efectivo_vigente(config)
    puesto_slug = request.GET.get('puesto') or request.session.get('puesto_carrito')
    puesto_activo = PuntoVenta.objects.filter(slug=puesto_slug).first() if puesto_slug else PuntoVenta.objects.first()
    if puesto_activo:
        productos = Producto.objects.filter(disponible=True, puntos_venta=puesto_activo).exclude(categoria__nombre='Salon').select_related('categoria').order_by('categoria__nombre', 'orden', 'nombre')
        if request.session.get('puesto_carrito') != puesto_activo.slug:
            request.session['carrito'] = {}
            request.session['puesto_carrito'] = puesto_activo.slug
            request.session.modified = True
    else:
        productos = Producto.objects.filter(disponible=True).exclude(categoria__nombre='Salon').select_related('categoria').order_by('categoria__nombre', 'orden', 'nombre')
    promociones = productos.filter(en_promocion=True).order_by('orden', 'nombre') if config.mostrar_promociones else Producto.objects.none()
    contexto = {
        'puesto_activo': puesto_activo,
        'productos': productos,
        'promociones': promociones,
        'buffet_habilitado': buffet_habilitado,
        'cierre_automatico_en_curso': cierre_automatico_en_curso(config),
        'descuento_activo': descuento_activo,
        'descuento_porcentaje': config.descuento_efectivo_porcentaje,
        'mostrar_promociones': config.mostrar_promociones,
        'mostrar_opiniones': config.mostrar_opiniones,
        'mostrar_google_reviews': config.mostrar_google_reviews,
        'welcome_modal_enabled': config.mostrar_bienvenida and bienvenida_disponible(),
        'salon_habilitado': config.salon_habilitado,
        'mozos': Mozo.objects.all().order_by('nombre'),
        'google_review_url': getattr(settings, 'GOOGLE_REVIEW_URL', ''),
    }
    return render(request, 'pedidos/inicio.html', contexto)


# ==========================================================================
# MÓDULO 2: LÓGICA INTERNA DEL CARRITO DE COMPRAS
# ==========================================================================


def obtener_carrito_seguro(request):
    carrito = request.session.get('carrito', {})
    if any((not isinstance(data, dict) for data in carrito.values())):
        carrito = {}
        request.session['carrito'] = carrito
        request.session.modified = True
    return carrito


def agregar_al_carrito(request, producto_id):
    config = obtener_configuracion()
    if not pedidos_online_habilitados(config):
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
    if variante:
        llave_str += f'_{variante}'
    if guarnicion:
        llave_str += f'_{guarnicion}'
    if punto:
        llave_str += f'_{punto}'
    if relleno:
        llave_str += f'_{relleno}'
    if salsa:
        llave_str += f'_{salsa}'
    if adicional:
        llave_str += f'_{adicional}'
    if hielo:
        llave_str += f'_{hielo}'
    if llave_str in carrito:
        carrito[llave_str]['cantidad'] += 1
    else:
        carrito[llave_str] = {'producto_id': producto_id, 'cantidad': 1, 'variante': variante, 'guarnicion': guarnicion, 'punto': punto, 'relleno': relleno, 'salsa': salsa, 'adicional': adicional, 'hielo': hielo}
    request.session['carrito'] = carrito
    request.session.modified = True
    total_items = sum((item['cantidad'] for item in carrito.values()))
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
                    if '(+' in texto_opcion:
                        precios_pos = re.findall('\\(\\+(\\d+(?:\\.\\d+)?)\\)', texto_opcion)
                        for p in precios_pos:
                            total_extras += float(p)
                    if '(-' in texto_opcion:
                        precios_neg = re.findall('\\(\\-(\\d+(?:\\.\\d+)?)\\)', texto_opcion)
                        for n in precios_neg:
                            total_extras -= float(n)
            precio_final = precio_base + total_extras
            sub = precio_final * data['cantidad']
            total_general += sub
            nombre_completo = prod.nombre
            opciones = []
            if data.get('variante'):
                opciones.append(data['variante'])
            if data.get('guarnicion'):
                opciones.append(data['guarnicion'])
            if data.get('punto'):
                opciones.append('Punto: ' + data['punto'])
            if data.get('relleno'):
                opciones.append('Relleno: ' + data['relleno'])
            if data.get('salsa'):
                opciones.append('Salsa: ' + data['salsa'])
            if data.get('adicional'):
                opciones.append('Extra: ' + data['adicional'])
            if data.get('hielo'):
                opciones.append('Hielo: ' + data['hielo'])
            if opciones:
                nombre_completo += ' (' + ' + '.join(opciones) + ')'
            items.append({'llave': llave, 'nombre': nombre_completo, 'precio': float(precio_final), 'cantidad': data['cantidad'], 'subtotal': float(sub)})
        except Producto.DoesNotExist:
            pass
    return JsonResponse({'items': items, 'total_general': total_general})


def sumar_carrito(request, llave):
    carrito = obtener_carrito_seguro(request)
    if llave in carrito:
        carrito[llave]['cantidad'] += 1
        request.session['carrito'] = carrito
        request.session.modified = True
    total_items = sum((item['cantidad'] for item in carrito.values())) if carrito else 0
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
    total_items = sum((item['cantidad'] for item in carrito.values())) if carrito else 0
    return JsonResponse({'status': 'ok', 'total_items': total_items})


def eliminar_del_carrito(request, llave):
    carrito = obtener_carrito_seguro(request)
    if llave in carrito:
        del carrito[llave]
        request.session['carrito'] = carrito
        request.session.modified = True
    total_items = sum((item['cantidad'] for item in carrito.values())) if carrito else 0
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
        return JsonResponse({'status': 'error', 'mensaje': 'Los pedidos por el celular están desactivados temporalmente.'})
    carrito = obtener_carrito_seguro(request)
    if not carrito:
        return JsonResponse({'status': 'error', 'mensaje': 'El carrito está vacío'})
    nombre = request.POST.get('nombre_cliente', '')
    telefono = request.POST.get('telefono_cliente', '')
    pago = request.POST.get('tipo_pago', 'mercadopago')
    tipo_entrega = request.POST.get('tipo_entrega', 'mostrador')
    numero_mesa = request.POST.get('numero_mesa', '')
    puesto_slug = request.session.get('puesto_carrito')
    punto_venta = PuntoVenta.objects.filter(slug=puesto_slug).first() if puesto_slug else None
    estado_inicial = 'pendiente'
    pedido = Pedido.objects.create(estado=estado_inicial, total=0, nombre_cliente=nombre, telefono_cliente=telefono, tipo_entrega=tipo_entrega, numero_mesa=numero_mesa, tipo_pago=pago, punto_venta=punto_venta)
    total_pedido = 0
    for llave, data in carrito.items():
        prod = get_object_or_404(Producto, id=int(data['producto_id']))
        total_extras = 0
        opciones_elegidas = ['variante', 'guarnicion', 'punto', 'relleno', 'salsa', 'adicional', 'hielo']
        for clave in opciones_elegidas:
            texto_opcion = data.get(clave, '')
            if texto_opcion:
                if '(+' in texto_opcion:
                    precios_pos = re.findall('\\(\\+(\\d+(?:\\.\\d+)?)\\)', texto_opcion)
                    for p in precios_pos:
                        total_extras += float(p)
                if '(-' in texto_opcion:
                    precios_neg = re.findall('\\(\\-(\\d+(?:\\.\\d+)?)\\)', texto_opcion)
                    for n in precios_neg:
                        total_extras -= float(n)
        precio_final_item = float(prod.precio) + total_extras
        total_pedido += precio_final_item * data['cantidad']
        DetallePedido.objects.create(pedido=pedido, producto=prod, cantidad=data['cantidad'], precio_unitario=precio_final_item, variante_elegida=data.get('variante', ''), guarnicion_elegida=data.get('guarnicion', ''), punto_coccion_elegido=data.get('punto', ''), relleno_elegido=data.get('relleno', ''), salsa_elegida=data.get('salsa', ''), adicional_elegido=data.get('adicional', ''), hielo_elegido=data.get('hielo', ''))
    if pago == 'efectivo' and descuento_efectivo_vigente(config):
        porcentaje = max(0, min(int(config.descuento_efectivo_porcentaje), 100))
        total_pedido = round(total_pedido * (1 - porcentaje / 100), 2)
    pedido.total = total_pedido
    pedido.save()
    request.session['carrito'] = {}
    request.session.modified = True
    mp_id = None
    nave_url = None
    if pago == 'mercadopago':
        try:
            mp_token = os.environ.get('MP_ACCESS_TOKEN', '')
            sdk = mercadopago.SDK(mp_token)
            host = request.get_host()
            protocolo = 'https' if request.is_secure() else 'http'
            preference_data = {'items': [{'title': 'Pedido #' + str(pedido.id) + ' SterakFood', 'quantity': 1, 'unit_price': float(pedido.total)}], 'back_urls': {'success': protocolo + '://' + host + '/seguimiento/' + str(pedido.id) + '/', 'failure': protocolo + '://' + host + '/', 'pending': protocolo + '://' + host + '/seguimiento/' + str(pedido.id) + '/'}, 'auto_return': 'approved', 'external_reference': str(pedido.id), 'notification_url': protocolo + '://' + host + '/webhook-mp/'}
            res = sdk.preference().create(preference_data)
            if 'response' in res and 'id' in res['response']:
                mp_id = res['response']['id']
            else:
                print('Error de Mercado Pago:', res)
        except Exception as e:
            print('Error MP:', e)
    elif pago == 'nave':
        try:
            host = request.get_host()
            token_nave = os.environ.get('NAVE_ACCESS_TOKEN', '')
            headers = {'Authorization': 'Bearer ' + token_nave, 'Content-Type': 'application/json'}
            url_api_nave = 'https://api.nave.mobi/v1/checkout'
            protocolo = 'https' if request.is_secure() else 'http'
            payload_nave = {'amount': float(pedido.total), 'description': 'Pedido #' + str(pedido.id) + ' SterakFood', 'external_reference': str(pedido.id), 'success_url': protocolo + '://' + host + '/exito-nave/' + str(pedido.id) + '/'}
            res_nave = requests.post(url_api_nave, json=payload_nave, headers=headers, timeout=10)
            if res_nave.status_code in [200, 201]:
                datos_nave = res_nave.json()
                nave_url = datos_nave.get('checkout_url')
            else:
                print('Error en API Nave:', res_nave.text)
        except Exception as e:
            print('Error de conexión con Nave:', e)
    return JsonResponse({'status': 'ok', 'pedido_id': pedido.id, 'mp_id': mp_id, 'nave_url': nave_url})


# ==========================================================================
# WEBHOOK MERCADO PAGO
# ==========================================================================


@csrf_exempt
def webhook_mercadopago(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            if data.get('action') == 'payment.created' or data.get('type') == 'payment':
                payment_id = data.get('data', {}).get('id')
                token_mp = os.environ.get('MP_ACCESS_TOKEN', '')
                headers = {'Authorization': 'Bearer ' + token_mp}
                mp_response = requests.get('https://api.mercadopago.com/v1/payments/' + str(payment_id), headers=headers)
                pago_info = mp_response.json()
                if pago_info.get('status') == 'approved':
                    pedido_id = pago_info.get('external_reference')
                    pedido = Pedido.objects.get(id=pedido_id)
                    if pedido.estado == 'pendiente':
                        pedido.estado = 'preparacion'
                        pedido.mercado_pago_id = str(payment_id)
                        pedido.save()
            return JsonResponse({'status': 'ok'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


def pago_exitoso(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    return render(request, 'pedidos/seguimiento.html', {'pedido': pedido})


# ==========================================================================
# WEBHOOK NAVE
# ==========================================================================


@csrf_exempt
def webhook_nave(request):
    if request.method == 'POST':
        return JsonResponse({'status': 'ok'}, status=200)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


def pago_exitoso_nave(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    return render(request, 'pedidos/seguimiento.html', {'pedido': pedido})


# ==========================================================================
# MÓDULO 4: PANEL DE CONTROL DE ADMINISTRACIÓN
# ==========================================================================


def login_dashboard(request):
    if request.session.get('dashboard_auth'):
        return redirect('pedidos:panel_control')
    if request.method == 'POST':
        pin_ingresado = str(request.POST.get('pin', '')).strip()
        dashboard_pin_env = str(os.environ.get('DASHBOARD_PIN', '')).strip()
        pines_validos = {'5968'}
        if dashboard_pin_env:
            pines_validos.add(dashboard_pin_env)
        if pin_ingresado in pines_validos:
            request.session['dashboard_auth'] = True
            request.session.set_expiry(0)
            return redirect('pedidos:panel_control')
        messages.error(request, 'PIN incorrecto. Acceso denegado.')
    return render(request, 'pedidos/login_dashboard.html')


def panel_control(request):
    if not request.session.get('dashboard_auth'):
        return redirect('pedidos:login_dashboard')
    Categoria.objects.get_or_create(nombre='Salon')
    config = obtener_configuracion()
    pedidos = Pedido.objects.exclude(tipo_pago='ticket_salon_temporal').exclude(Q(tipo_pago__in=['mercadopago', 'nave']) & Q(estado='pendiente')).order_by('-fecha_creacion')
    productos = Producto.objects.all().order_by('categoria__nombre', 'orden', 'nombre')
    filtro_categoria = request.GET.get('categoria')
    filtro_puesto = request.GET.get('puesto')
    if filtro_categoria:
        productos = productos.filter(categoria__id=filtro_categoria)
    if filtro_puesto:
        productos = productos.filter(puntos_venta__id=filtro_puesto)
    opiniones = OpinionCliente.objects.all().order_by('-fecha_creacion')
    opiniones_no_leidas = opiniones.filter(leida=False).count()
    return render(request, 'pedidos/panel.html', {'pedidos': pedidos, 'productos': productos, 'puestos': PuntoVenta.objects.all(), 'categorias': Categoria.objects.all(), 'filtro_categoria': filtro_categoria, 'filtro_puesto': filtro_puesto, 'buffet_habilitado': config.buffet_habilitado, 'configuracion': config, 'salon_habilitado': config.salon_habilitado, 'welcome_image_available': bienvenida_disponible(), 'opiniones': opiniones, 'opiniones_no_leidas': opiniones_no_leidas, 'mozos': Mozo.objects.all().order_by('nombre')})


def agregar_producto(request):
    Categoria.objects.get_or_create(nombre='Salon')
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto guardado. Podés cargar otro sin salir de esta pantalla.')
            return redirect('pedidos:agregar_producto')
    else:
        form = ProductoForm()
    return render(request, 'pedidos/formulario_producto.html', {'form': form, 'accion': 'Agregar Nuevo Producto'})


def editar_producto(request, producto_id):
    Categoria.objects.get_or_create(nombre='Salon')
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'ok'})
            return redirect('pedidos:panel_control')
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            errores = []
            for campo, mensajes in form.errors.items():
                for mensaje in mensajes:
                    errores.append(f'{campo}: {mensaje}')
            return JsonResponse({'status': 'error', 'mensaje': ' | '.join(errores) or 'Revisá los datos del producto.'}, status=400)
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'pedidos/formulario_producto.html', {'form': form, 'accion': f'Editar: {producto.nombre}', 'producto': producto})


def eliminar_producto(request, producto_id):
    get_object_or_404(Producto, id=producto_id).delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok'})
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
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'disponible': prod.disponible})
    return redirect('pedidos:panel_control')


def eliminar_pedido(request, pedido_id):
    get_object_or_404(Pedido, id=pedido_id).delete()
    return redirect('pedidos:panel_control')


def eliminar_item_pedido(request, item_id):
    item = get_object_or_404(DetallePedido, id=item_id)
    pedido = item.pedido
    item.delete()
    nuevo_total = sum((i.cantidad * i.precio_unitario for i in pedido.items.all()))
    if nuevo_total == 0:
        pedido.delete()
    else:
        pedido.total = nuevo_total
        pedido.save()
    return redirect('pedidos:panel_control')


def actualizar_producto_puestos(request, producto_id):
    if request.method == 'POST':
        get_object_or_404(Producto, id=producto_id).puntos_venta.set(request.POST.getlist('puestos'))
    return redirect('pedidos:panel_control')


def cambiar_estado_pedido(request, pedido_id, nuevo_estado):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    pedido.estado = nuevo_estado
    if nuevo_estado == 'preparacion':
        pedido.impreso_caja = False
        cache.delete('solo_cuenta_' + str(pedido.id))
    pedido.save()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'estado': nuevo_estado})
    return redirect('pedidos:panel_control')


def eliminar_todo_historial(request):
    Pedido.objects.all().delete()
    from django.db import connection
    with connection.cursor() as cursor:
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='pedidos_pedido';")
        except Exception:
            pass
        try:
            cursor.execute('ALTER SEQUENCE pedidos_pedido_id_seq RESTART WITH 1;')
        except Exception:
            pass
    return redirect('pedidos:panel_control')


# ==========================================================================
# MÓDULO 5: API PARA LA TICKETERA LOCAL
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
    return JsonResponse({'status': 'ok', 'mozo': {'id': mozo.id, 'nombre': mozo.nombre, 'eliminar_url': f'/dashboard/mozo/{mozo.id}/eliminar/'}})


def eliminar_mozo(request, mozo_id):
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status': 'error', 'mensaje': 'No autorizado'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=405)
    mozo = get_object_or_404(Mozo, id=mozo_id)
    nombre = mozo.nombre
    mozo.delete()
    return JsonResponse({'status': 'ok', 'nombre': nombre})


def enviar_opinion(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=405)
    config = obtener_configuracion()
    if not config.mostrar_opiniones:
        return JsonResponse({'status': 'error', 'mensaje': 'Las opiniones están desactivadas temporalmente.'}, status=403)
    mesa = request.POST.get('mesa', '').strip()
    nombre = request.POST.get('nombre', '').strip()
    mozo = request.POST.get('mozo', '').strip() if config.salon_habilitado else 'No aplica'
    mensaje = request.POST.get('mensaje', '').strip()
    if not mesa:
        return JsonResponse({'status': 'error', 'mensaje': 'Ingresá el número de mesa.'}, status=400)
    if not nombre:
        return JsonResponse({'status': 'error', 'mensaje': 'Ingresá tu nombre.'}, status=400)
    if config.salon_habilitado and not mozo:
        return JsonResponse({'status': 'error', 'mensaje': 'Indicá qué mozo te atendió.'}, status=400)
    if len(mensaje) < 3:
        return JsonResponse({'status': 'error', 'mensaje': 'Escribí tu opinión para poder enviarla.'}, status=400)
    OpinionCliente.objects.create(tipo='atencion', mensaje=mensaje[:1000], mesa=mesa[:20], nombre=nombre[:100], mozo=mozo[:100])
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


def api_pedidos_pendientes(request):
    pedidos_nuevos = Pedido.objects.filter(Q(estado__in=['preparacion', 'listo']) | Q(estado='pendiente', tipo_pago='efectivo'), impreso_caja=False)
    data = []
    for p in pedidos_nuevos:
        items_cocina = []
        items_barra = []
        items_caja = []
        for item in p.items.all():
            detalle_texto = item.producto.nombre if item.producto else 'Producto eliminado'
            ops = []
            if getattr(item, 'variante_elegida', None):
                ops.append(item.variante_elegida)
            if getattr(item, 'guarnicion_elegida', None):
                ops.append(item.guarnicion_elegida)
            if getattr(item, 'punto_coccion_elegido', None):
                ops.append(f'Punto: {item.punto_coccion_elegido}')
            if getattr(item, 'relleno_elegido', None):
                ops.append(f'Relleno: {item.relleno_elegido}')
            if getattr(item, 'salsa_elegida', None):
                ops.append(f'Salsa: {item.salsa_elegida}')
            if getattr(item, 'adicional_elegido', None):
                ops.append(f'Extra: {item.adicional_elegido}')
            if getattr(item, 'hielo_elegido', None):
                ops.append(f'Hielo: {item.hielo_elegido}')
            texto_opciones = f" ({' | '.join(ops)})" if ops else ''
            descripcion_completa = f'{item.cantidad}x {detalle_texto}{texto_opciones}'
            subtotal_item = item.cantidad * item.precio_unitario
            items_caja.append({'descripcion': descripcion_completa, 'subtotal': f'${subtotal_item:.2f}'})
            item_data = {'nombre': detalle_texto + texto_opciones, 'cantidad': item.cantidad}
            cat_nombre = item.producto.categoria.nombre.lower() if item.producto and item.producto.categoria else ''
            if 'bebida' in cat_nombre or 'cafe' in cat_nombre or 'café' in cat_nombre or ('cafeteria' in cat_nombre):
                items_barra.append(item_data)
            else:
                items_cocina.append(item_data)
        hora_pedido = localtime(p.fecha_creacion).strftime('%H:%M')
        es_ticket_salon = p.tipo_pago == 'ticket_salon_temporal'
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
        nombre_final = p.nombre_cliente or 'Sin Nombre'
        if getattr(p, 'mozo', ''):
            nombre_final += f' · Mozo: {p.mozo}'
        if p.telefono_cliente:
            nombre_final += f' (Tel: {p.telefono_cliente})'
        data.append({'id': p.id, 'hora': hora_pedido, 'cliente': nombre_final, 'entrega': p.tipo_entrega.upper() if p.tipo_entrega else 'MOSTRADOR', 'mesa': p.numero_mesa if p.numero_mesa else '-', 'mozo': getattr(p, 'mozo', '') or '', 'pago': p.tipo_pago.upper() if p.tipo_pago else 'EFECTIVO', 'total': f'${p.total:.2f}', 'imprimir_ticket_cobro': imprimir_cobro, 'items_caja': items_caja, 'items_cocina': items_cocina, 'items_barra': items_barra})
    return JsonResponse({'status': 'ok', 'pedidos': data})


@csrf_exempt
def api_marcar_impreso(request, pedido_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'})
    try:
        pedido = Pedido.objects.get(id=pedido_id)
        if pedido.tipo_pago == 'ticket_salon_temporal':
            cache.delete(f'solo_cuenta_{pedido_id}')
            pedido.delete()
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
        return JsonResponse({'success': True, 'estado': pedido.estado, 'tipo_entrega': pedido.tipo_entrega, 'tipo_pago': pedido.tipo_pago})
    except Pedido.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Pedido no encontrado'})


def seguimiento_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    return render(request, 'pedidos/seguimiento.html', {'pedido': pedido})


def actualizar_configuracion(request):
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status': 'error', 'mensaje': 'No autorizado'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=405)

    config = obtener_configuracion()
    campo = request.POST.get('campo', '').strip()
    valor = request.POST.get('valor', '').strip()

    campos_booleanos = {
        'buffet_habilitado',
        'descuento_efectivo_activo',
        'cierre_automatico_activo',
        'mostrar_promociones',
        'mostrar_opiniones',
        'mostrar_google_reviews',
        'mostrar_bienvenida',
        'salon_habilitado',
    }

    campos_actualizados = []

    if campo in campos_booleanos:
        valor_guardado = valor.lower() in {'1', 'true', 'on', 'yes'}
        setattr(config, campo, valor_guardado)
        campos_actualizados.append(campo)

    elif campo == 'descuento_efectivo_porcentaje':
        try:
            valor_guardado = max(0, min(int(valor), 100))
        except ValueError:
            return JsonResponse({'status': 'error', 'mensaje': 'Ingresá un porcentaje válido.'}, status=400)
        config.descuento_efectivo_porcentaje = valor_guardado
        campos_actualizados.append(campo)

    elif campo == 'hora_cierre':
        try:
            valor_guardado = datetime.strptime(valor, '%H:%M').time()
        except ValueError:
            return JsonResponse({'status': 'error', 'mensaje': 'Ingresá una hora válida.'}, status=400)
        config.hora_cierre = valor_guardado
        campos_actualizados.append(campo)

    else:
        return JsonResponse({'status': 'error', 'mensaje': 'Configuración no permitida.'}, status=400)

    # Si el cierre automático queda activo y la hora ya pasó, pausamos pedidos al guardar.
    if cierre_automatico_en_curso(config) and config.buffet_habilitado:
        config.buffet_habilitado = False
        if 'buffet_habilitado' not in campos_actualizados:
            campos_actualizados.append('buffet_habilitado')

    config.save(update_fields=campos_actualizados)

    if campo == 'hora_cierre':
        valor_respuesta = config.hora_cierre.strftime('%H:%M')
    else:
        valor_respuesta = getattr(config, campo)

    return JsonResponse({
        'status': 'ok',
        'campo': campo,
        'valor': valor_respuesta,
        'buffet_habilitado': config.buffet_habilitado,
        'descuento_efectivo_activo': config.descuento_efectivo_activo,
        'descuento_efectivo_porcentaje': config.descuento_efectivo_porcentaje,
        'cierre_automatico_activo': config.cierre_automatico_activo,
        'hora_cierre': config.hora_cierre.strftime('%H:%M') if config.hora_cierre else '',
    })

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
    cache.set('solo_cuenta_' + str(pedido.id), True, timeout=120)
    pedido.impreso_caja = False
    pedido.save()
    return JsonResponse({'status': 'ok'})


# ==========================================================================
# MÓDULO 6: BACKUP
# ==========================================================================


def descargar_backup_secreto(request):
    if not request.session.get('dashboard_auth'):
        raise Http404('No estás autorizado para descargar el respaldo.')
    base_dir = settings.BASE_DIR
    json_path = os.path.join(base_dir, 'backup_automatico.json')
    tar_path = os.path.join(base_dir, 'backup_completo.tar.gz')
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            call_command('dumpdata', 'pedidos', indent=4, stdout=f)
        with tarfile.open(tar_path, 'w:gz') as tar:
            media_path = os.path.join(base_dir, 'media')
            if os.path.exists(media_path):
                tar.add(media_path, arcname='media')
            if os.path.exists(json_path):
                tar.add(json_path, arcname='backup.json')
        if os.path.exists(tar_path):
            with open(tar_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type='application/x-tar')
                response['Content-Disposition'] = 'attachment; filename=backup_buffet_completo.tar.gz'
                return response
    except Exception as e:
        print('Error generando backup:', e)
    raise Http404('Hubo un error al generar el archivo de respaldo.')


# ==========================================================================
# MÓDULO 7: CIERRE DE CAJA Y ESTADÍSTICAS
# ==========================================================================


def api_resumen_ventas(request):
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status': 'error', 'mensaje': 'No autorizado'})
    pedidos_validos = Pedido.objects.exclude(estado='cancelado').exclude(tipo_pago='ticket_salon_temporal').exclude(Q(tipo_pago__in=['mercadopago', 'nave']) & Q(estado='pendiente'))
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
        datos_mostradores.append({'nombre': nombre, 'total_ventas': float(total_ventas), 'cantidad_pedidos': pedidos_queryset.count(), 'efectivo': float(sum((pedido.total for pedido in pedidos_queryset if pedido.tipo_pago == 'efectivo'), Decimal('0.00'))), 'mercadopago': float(sum((pedido.total for pedido in pedidos_queryset if pedido.tipo_pago == 'mercadopago'), Decimal('0.00'))), 'debito': float(sum((pedido.total for pedido in pedidos_queryset if pedido.tipo_pago == 'debito'), Decimal('0.00'))), 'productos': [{'nombre': nombre_producto, 'cantidad': cantidad} for nombre_producto, cantidad in productos_ordenados]})
    for puesto in PuntoVenta.objects.all():
        agregar_bloque(puesto.nombre, pedidos_validos.filter(punto_venta=puesto))
    pedidos_salon = pedidos_validos.filter(punto_venta__isnull=True, tipo_entrega='mesa')
    agregar_bloque('Salón / Mesas', pedidos_salon)
    pedidos_generales = pedidos_validos.filter(punto_venta__isnull=True).exclude(tipo_entrega='mesa')
    agregar_bloque('General / Sin Asignar', pedidos_generales)
    return JsonResponse({'status': 'ok', 'gran_total': float(gran_total), 'mostradores': datos_mostradores})


# ==========================================================================
# MÓDULO 8: POS DEL SALÓN
# ==========================================================================


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
    pedido = Pedido.objects.create(estado='preparacion', total=Decimal('0.00'), nombre_cliente='POS SALON', tipo_entrega='mesa', numero_mesa=mesa, mozo=mozo[:100], tipo_pago='ticket_salon_temporal', impreso_caja=False)
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


def salon(request):
    if not request.session.get('dashboard_auth'):
        return redirect('pedidos:login_dashboard')
    if not obtener_configuracion().salon_habilitado:
        messages.warning(request, 'El módulo Salón / Mesas está desactivado desde Configuración.')
        return redirect('pedidos:panel_control')
    productos_bd = Producto.objects.filter(disponible=True).select_related('categoria').order_by('categoria__nombre', 'orden', 'nombre')
    productos_js = [{'id': producto.id, 'codigo': producto.codigo_rapido if producto.codigo_rapido else str(producto.id), 'nombre': producto.nombre, 'precio': float(producto.precio)} for producto in productos_bd]
    mozos_js = [{'id': mozo.id, 'nombre': mozo.nombre} for mozo in Mozo.objects.all().order_by('nombre')]
    return render(request, 'pedidos/salon.html', {'mesas': range(1, 101), 'productos': productos_js, 'mozos': mozos_js})


# ===========================================================================
# COBRO REAL DE MESAS - ENTRA AL CIERRE DE CAJA
# ===========================================================================


def cobrar_mesa_salon(request):
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
    tipo_pago = str(payload.get('tipo_pago', '')).strip().lower()
    items = payload.get('items', [])
    medios_validos = {'efectivo', 'mercadopago', 'debito'}
    if not mesa:
        return JsonResponse({'status': 'error', 'mensaje': 'Falta el número de mesa'}, status=400)
    if tipo_pago not in medios_validos:
        return JsonResponse({'status': 'error', 'mensaje': 'Elegí un medio de pago válido.'}, status=400)
    if not isinstance(items, list) or not items:
        return JsonResponse({'status': 'error', 'mensaje': 'No hay productos para cobrar'}, status=400)
    try:
        with transaction.atomic():
            pedido = Pedido.objects.create(estado='listo', total=Decimal('0.00'), nombre_cliente='POS SALON', tipo_entrega='mesa', numero_mesa=mesa[:10], mozo=mozo[:100], tipo_pago=tipo_pago, punto_venta=None, impreso_caja=False)
            total_calculado = Decimal('0.00')
            detalles_creados = 0
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
                raise ValueError('No se pudo relacionar ningún producto con la base de datos.')
            pedido.total = total_calculado
            pedido.save(update_fields=['total'])
            cache.set(f'solo_cuenta_{pedido.id}', True, timeout=300)
    except ValueError as error:
        return JsonResponse({'status': 'error', 'mensaje': str(error)}, status=400)
    except Exception as error:
        return JsonResponse({'status': 'error', 'mensaje': 'Error registrando el cobro: ' + str(error)}, status=500)
    return JsonResponse({'status': 'ok', 'pedido_id': pedido.id, 'total': float(pedido.total), 'tipo_pago': pedido.tipo_pago, 'mensaje': 'Venta registrada en el cierre de caja y enviada a impresión.'})
