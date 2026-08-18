import json
import re  
import requests
import urllib.parse
import os
import tarfile
import mercadopago
from django.conf import settings
from django.core.management import call_command
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, Http404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import localtime  
from django.utils import timezone # 🔥 IMPORTANTE PARA EL RELOJ DEL DESCUENTO 🔥
from django.core.cache import cache  
from .forms import ProductoForm
from .models import Producto, Pedido, DetallePedido, PuntoVenta, Categoria, Configuracion
from django.core.exceptions import PermissionDenied

# ==========================================================================
# MÓDULO 1: VISTAS DEL CLIENTE (MENÚ PÚBLICO)
# ==========================================================================

def inicio(request):
    config = Configuracion.objects.first()
    buffet_habilitado = config.buffet_habilitado if config else True
    
    # 🔥 MAGIA: LÓGICA AUTOMÁTICA DEL DESCUENTO 🔥
    hora_actual = timezone.localtime(timezone.now())
    es_finde = hora_actual.weekday() in [5, 6]  # 5 = Sábado, 6 = Domingo
    es_horario = 12 <= hora_actual.hour < 15    # De 12:00 a 14:59 hs
    descuento_activo = es_finde and es_horario
    
    # 🔥 CAMBIO PORTAFOLIO: Tomamos el primer puesto automáticamente y no pedimos URL 🔥
    puesto_activo = PuntoVenta.objects.first()
    
    # Si hay un puesto creado, filtramos por él y guardamos en sesión
    if puesto_activo:
        productos = Producto.objects.filter(disponible=True, puntos_venta=puesto_activo).select_related('categoria').order_by('categoria__nombre')
        
        if request.session.get('puesto_carrito') != puesto_activo.slug:
            request.session['carrito'] = {} # Limpiamos si había basura
            request.session['puesto_carrito'] = puesto_activo.slug
            request.session.modified = True
    else:
        # Si por alguna razón la base de datos está vacía y no hay puestos, mostramos todo
        productos = Producto.objects.filter(disponible=True).select_related('categoria').order_by('categoria__nombre')

    return render(request, 'pedidos/inicio.html', {
        'puesto_activo': puesto_activo, 
        'productos': productos,
        'buffet_habilitado': buffet_habilitado,
        'descuento_activo': descuento_activo 
    })

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
    config = Configuracion.objects.first()
    if config and not config.buffet_habilitado:
        return JsonResponse({'status': 'error', 'mensaje': 'Los pedidos por el celular estan desactivados por alta demanda.'})

    carrito = obtener_carrito_seguro(request)
    if not carrito: return JsonResponse({'status': 'error', 'mensaje': 'El carrito está vacío'})

    nombre = request.POST.get('nombre_cliente', '')
    telefono = request.POST.get('telefono_cliente', '')
    pago = request.POST.get('tipo_pago', 'mercadopago')
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
    
    pedido.total = total_pedido
    pedido.save()

    request.session['carrito'] = {}
    request.session.modified = True

    mp_id = None
    nave_url = None

    if pago == 'mercadopago':
        try:
            # LEEMOS EL TOKEN DESDE EL
            mp_token = os.environ.get('MP_ACCESS_TOKEN')
            sdk = mercadopago.SDK(mp_token)
            
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
            # 🔥 LEEMOS EL TOKEN DESDE EL .ENV (si lo usás a futuro) 🔥
            TOKEN_NAVE = os.environ.get('NAVE_ACCESS_TOKEN', 'TU_TOKEN_SECRETO_DE_NAVE_ACA') 
            
            headers = {
                "Authorization": f"Bearer {TOKEN_NAVE}",
                "Content-Type": "application/json"
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
                
                # 🔥 LEEMOS EL TOKEN DESDE EL .ENV 🔥
                token_mp = os.environ.get('MP_ACCESS_TOKEN')
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
    if request.session.get('dashboard_auth'): return redirect('pedidos:panel_control')
    if request.method == 'POST':
        if request.POST.get('pin') == '5968':
            request.session['dashboard_auth'] = True
            
            #  ESTO HACE QUE LA SESIÓN DEL PANEL EXPIRE AL CERRAR EL NAVEGADOR 
            request.session.set_expiry(0) 
            
            return redirect('pedidos:panel_control')
        else: messages.error(request, "PIN incorrecto. Acceso denegado.")
    return render(request, 'pedidos/login_dashboard.html')

def panel_control(request):
    if not request.session.get('dashboard_auth'): return redirect('pedidos:login_dashboard')
    
    config, created = Configuracion.objects.get_or_create(id=1)

    pedidos = Pedido.objects.all().order_by('-fecha_creacion')
    productos = Producto.objects.all().order_by('categoria__nombre', 'nombre')
    
    filtro_categoria = request.GET.get('categoria')
    filtro_puesto = request.GET.get('puesto')
    if filtro_categoria: productos = productos.filter(categoria__id=filtro_categoria)
    if filtro_puesto: productos = productos.filter(puntos_venta__id=filtro_puesto)

    return render(request, 'pedidos/panel.html', {
        'pedidos': pedidos, 
        'productos': productos, 
        'puestos': PuntoVenta.objects.all(),
        'categorias': Categoria.objects.all(), 
        'filtro_categoria': filtro_categoria, 
        'filtro_puesto': filtro_puesto,
        'buffet_habilitado': config.buffet_habilitado,
    })

def agregar_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('pedidos:panel_control')
    else:
        form = ProductoForm()
    
    return render(request, 'pedidos/formulario_producto.html', {
        'form': form, 
        'accion': 'Agregar Nuevo Producto'
    })

def editar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            return redirect('pedidos:panel_control')
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
        
        # 🔥 EL TRUCO: Reemplazamos la coma por punto antes de guardar
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
    # 1. Borramos todos los pedidos (Django también borra los detalles en cascada)
    Pedido.objects.all().delete()
    
    # 2. Inyectamos SQL directo para reiniciar el contador a 1
    from django.db import connection
    with connection.cursor() as cursor:
        # Intento 1: Reseteo para SQLite (Entorno local)
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='pedidos_pedido';")
        except:
            pass
            
        # Intento 2: Reseteo para PostgreSQL
        try:
            cursor.execute("ALTER SEQUENCE pedidos_pedido_id_seq RESTART WITH 1;")
        except:
            pass
            
    return redirect('pedidos:panel_control')

# ==========================================================================
# MÓDULO 5: API PARA LA TICKETERA LOCAL (IMPRESORA) Y PANTALLA ESTADO
# ==========================================================================

def api_pedidos_pendientes(request):
    from django.db.models import Q
    
    pedidos_nuevos = Pedido.objects.filter(
        Q(estado__in=['preparacion', 'listo']) | Q(estado='pendiente', tipo_pago='efectivo'),
        impreso_caja=False
    )
    data = []
    
    for p in pedidos_nuevos:
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
            
            item_data = {'nombre': detalle_texto + texto_opciones, 'cantidad': item.cantidad}
            
            cat_nombre = item.producto.categoria.nombre.lower() if item.producto.categoria else ""
            if "bebida" in cat_nombre or "cafe" in cat_nombre or "café" in cat_nombre or "cafeteria" in cat_nombre:
                items_barra.append(item_data)
            else:
                items_cocina.append(item_data)

        hora_pedido = localtime(p.fecha_creacion).strftime('%H:%M')
        
        es_solo_cuenta = cache.get(f'solo_cuenta_{p.id}')
        if es_solo_cuenta:
            items_cocina = [] 
            items_barra = []   
            imprimir_cobro = True
        else:
            imprimir_cobro = (p.tipo_pago == 'efectivo' and p.estado == 'pendiente')

        data.append({
            'id': p.id,
            'hora': hora_pedido,
            'cliente': p.nombre_cliente or "Sin Nombre",
            'entrega': p.tipo_entrega.upper() if p.tipo_entrega else "MOSTRADOR",
            'mesa': p.numero_mesa if p.numero_mesa else '-',
            'pago': p.tipo_pago.upper() if p.tipo_pago else "EFECTIVO",
            'total': f"${p.total:.2f}",
            'imprimir_ticket_cobro': imprimir_cobro,  
            'items_caja': items_caja,                 
            'items_cocina': items_cocina,
            'items_barra': items_barra
        })
    
    return JsonResponse({'status': 'ok', 'pedidos': data})

@csrf_exempt
def api_marcar_impreso(request, pedido_id):
    if request.method == 'POST':
        try:
            pedido = Pedido.objects.get(id=pedido_id)
            pedido.impreso_caja = True
            pedido.save()
            cache.delete(f'solo_cuenta_{pedido_id}')
            return JsonResponse({'status': 'ok'})
        except Pedido.DoesNotExist: return JsonResponse({'status': 'error', 'mensaje': 'Pedido no encontrado'})
    return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'})

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

def cambiar_estado_global(request):
    if not request.session.get('dashboard_auth'): 
        return redirect('pedidos:login_dashboard')
    
    config, created = Configuracion.objects.get_or_create(id=1)
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

#descargar backup menu (Versión Automática)
def descargar_backup_secreto(request):
    # Por seguridad: si no está logueado en el panel, lo saca
    if not request.session.get('dashboard_auth'): 
        raise Http404("No estás autorizado para descargar el respaldo.")

    base_dir = settings.BASE_DIR
    json_path = os.path.join(base_dir, 'backup_automatico.json')
    tar_path = os.path.join(base_dir, 'backup_completo.tar.gz')
    
    try:
        # 1. Arma un JSON con todo tu menú actualizado
        with open(json_path, 'w', encoding='utf-8') as f:
            call_command('dumpdata', 'pedidos', indent=4, stdout=f)
        
        # 2. Comprime ese JSON junto con todas las fotos de la carpeta "media"
        with tarfile.open(tar_path, "w:gz") as tar:
            if os.path.exists(os.path.join(base_dir, 'media')):
                tar.add(os.path.join(base_dir, 'media'), arcname='media')
            if os.path.exists(json_path):
                tar.add(json_path, arcname='backup.json')
                
        # 3. Fuerza la descarga en el navegador
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
    
    # Filtramos pedidos válidos (ignoramos los cancelados)
    pedidos_validos = Pedido.objects.exclude(estado='cancelado')
    puestos = PuntoVenta.objects.all()
    
    datos_mostradores = []
    gran_total = 0
    
    # Iteramos por cada mostrador que tengas creado
    for puesto in puestos:
        pedidos_puesto = pedidos_validos.filter(punto_venta=puesto)
        
        # Ignoramos los mostradores que no tuvieron ventas hoy para mantener el panel limpio
        if not pedidos_puesto.exists():
            continue
            
        total_ventas = sum(p.total for p in pedidos_puesto)
        gran_total += total_ventas
        cantidad_pedidos = pedidos_puesto.count()
        
        ventas_efectivo = sum(p.total for p in pedidos_puesto if p.tipo_pago == 'efectivo')
        ventas_mp = sum(p.total for p in pedidos_puesto if p.tipo_pago == 'mercadopago')
        ventas_nave = sum(p.total for p in pedidos_puesto if p.tipo_pago == 'nave')
        
        # Contamos los productos específicos vendidos en ESTE mostrador
        detalles = DetallePedido.objects.filter(pedido__in=pedidos_puesto)
        productos_vendidos = {}
        for d in detalles:
            nombre = d.producto.nombre
            productos_vendidos[nombre] = productos_vendidos.get(nombre, 0) + d.cantidad
            
        # Ordenamos de mayor a menor
        productos_ordenados = sorted(productos_vendidos.items(), key=lambda x: x[1], reverse=True)
        
        datos_mostradores.append({
            'nombre': puesto.nombre,
            'total_ventas': float(total_ventas),
            'cantidad_pedidos': cantidad_pedidos,
            'efectivo': float(ventas_efectivo),
            'mercadopago': float(ventas_mp),
            'nave': float(ventas_nave),
            'productos': [{'nombre': k, 'cantidad': v} for k, v in productos_ordenados]
        })

    # Por si quedó algún pedido "huérfano" sin mostrador asignado
    pedidos_sin_puesto = pedidos_validos.filter(punto_venta__isnull=True)
    if pedidos_sin_puesto.exists():
        total_ventas = sum(p.total for p in pedidos_sin_puesto)
        gran_total += total_ventas
        detalles = DetallePedido.objects.filter(pedido__in=pedidos_sin_puesto)
        productos_vendidos = {}
        for d in detalles:
            nombre = d.producto.nombre
            productos_vendidos[nombre] = productos_vendidos.get(nombre, 0) + d.cantidad
        productos_ordenados = sorted(productos_vendidos.items(), key=lambda x: x[1], reverse=True)
        
        datos_mostradores.append({
            'nombre': 'General / Sin Asignar',
            'total_ventas': float(total_ventas),
            'cantidad_pedidos': pedidos_sin_puesto.count(),
            'efectivo': float(sum(p.total for p in pedidos_sin_puesto if p.tipo_pago == 'efectivo')),
            'mercadopago': float(sum(p.total for p in pedidos_sin_puesto if p.tipo_pago == 'mercadopago')),
            'nave': float(sum(p.total for p in pedidos_sin_puesto if p.tipo_pago == 'nave')),
            'productos': [{'nombre': k, 'cantidad': v} for k, v in productos_ordenados]
        })

    return JsonResponse({
        'status': 'ok',
        'gran_total': float(gran_total),
        'mostradores': datos_mostradores
    })