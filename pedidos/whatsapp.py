import requests
from .models import Pedido

# ==========================================
# CONFIGURACIÓN DE GREEN API
# ==========================================
API_URL = "https://7107.api.greenapi.com"
ID_INSTANCE = "7107648073"
API_TOKEN = "8f6a296ff1554db0b8c5daaa8fcd14170e50cd11c0d24980bc" 

def _enviar_mensaje_green_api(telefono_cliente, mensaje_texto):
    num_limpio = str(telefono_cliente).replace("+", "").replace(" ", "").replace("-", "").strip()
    if num_limpio.startswith("0"):
        num_limpio = num_limpio[1:]
        
    if len(num_limpio) == 10:
        num_limpio = "549" + num_limpio
    elif num_limpio.startswith("54") and not num_limpio.startswith("549"):
        num_limpio = num_limpio.replace("54", "549", 1)
        
    chat_id = f"{num_limpio}@c.us"
    url = f"{API_URL}/waInstance{ID_INSTANCE}/sendMessage/{API_TOKEN}"

    payload = {"chatId": chat_id, "message": mensaje_texto}
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"✅ Green API: Mensaje enviado a {chat_id}")
            return True
        else:
            print(f"❌ Error en Green API: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Falló la conexión: {e}")
        return False

def _armar_detalle_items(pedido):
    lineas = []
    for item in pedido.items.all():
        texto_item = f"🔸 {item.cantidad}x {item.producto.nombre}"
        ops = []
        if item.variante_elegida: ops.append(item.variante_elegida)
        if item.guarnicion_elegida: ops.append(item.guarnicion_elegida)
        if item.punto_coccion_elegido: ops.append(f"Punto: {item.punto_coccion_elegido}")
        if item.relleno_elegido: ops.append(f"Relleno: {item.relleno_elegido}")
        
        if ops:
            texto_item += f" ({' | '.join(ops)})"
        lineas.append(texto_item)
    return "\n".join(lineas)

# ==========================================
# DISPARADORES CON FORMATO META (WHATSAPP BUSINESS)
# ==========================================

def notificar_nuevo_pedido(pedido_id):
    try:
        pedido = Pedido.objects.get(id=pedido_id)
        detalle = _armar_detalle_items(pedido)
        pago_texto = "MercadoPago 📱" if pedido.tipo_pago == 'mercadopago' else "Efectivo/Transferencia 💵"
        
        # 🔥 ACÁ LIMPIAMOS EL NOMBRE PARA EL WHATSAPP
        nombre_limpio = pedido.nombre_cliente.split(" (Nota:")[0] if pedido.nombre_cliente else "Cliente"
        
        texto = (
            f"🇸🇱 *BUFFET SAN MARTÍN* 🇸🇱\n\n"
            f"¡Hola {nombre_limpio}! 👋\n"
            f"Recibimos tu pedido *#{pedido.id}* y ya lo estamos preparando 👨‍🍳🔥\n\n"
            f"*Detalle de tu pedido:*\n"
            f"{detalle}\n\n"
            f"💰 *Total:* ${pedido.total}\n"
            f"💳 *Abonado mediante:* {pago_texto}\n\n"
            f"⏳ Te avisamos por este mismo medio cuando esté listo. ¡Gracias!"
        )
        return _enviar_mensaje_green_api(pedido.telefono_cliente, texto)
    except Exception as e:
        print(f"Error Whatsapp (Nuevo Pedido): {e}")


def notificar_pago_procesado(pedido_id):
    try:
        pedido = Pedido.objects.get(id=pedido_id)
        detalle = _armar_detalle_items(pedido)
        
        #  ACÁ LIMPIAMOS EL NOMBRE PARA EL WHATSAPP
        nombre_limpio = pedido.nombre_cliente.split(" (Nota:")[0] if pedido.nombre_cliente else "Cliente"
        
        texto = (
            f"🇸🇱 *BUFFET SAN MARTÍN* 🇸🇱\n\n"
            f"¡Pago confirmado, {nombre_limpio}! ✅\n"
            f"Tu pedido *#{pedido.id}* ya ingresó a la cocina 👨‍🍳🔥\n\n"
            f"*Detalle de tu pedido:*\n"
            f"{detalle}\n\n"
            f"💰 *Total:* ${pedido.total}\n"
            f"💳 *Abonado mediante:* MercadoPago 📱\n\n"
            f"⏳ Te avisamos apenas puedas venir a buscarlo. ¡Gracias!"
        )
        return _enviar_mensaje_green_api(pedido.telefono_cliente, texto)
    except Exception as e:
        print(f"Error Whatsapp (Pago Procesado): {e}")


def notificar_pedido_listo(pedido_id):
    try:
        pedido = Pedido.objects.get(id=pedido_id)
        slug_puesto = pedido.punto_venta.slug.lower() if pedido.punto_venta else ''
        tipo = pedido.tipo_entrega.lower() if pedido.tipo_entrega else 'mostrador'
        
        # ACÁ LIMPIAMOS EL NOMBRE PARA EL WHATSAPP
        nombre_limpio = pedido.nombre_cliente.split(" (Nota:")[0] if pedido.nombre_cliente else "Cliente"
        
        if 'parrilla' in slug_puesto or 'foodtruck' in slug_puesto:
            texto_entrega = "¡Ya podés venir a retirar tu pedido por el puesto!"
        elif tipo == 'mesa':
            texto_entrega = f"¡El mozo te está llevando todo tu pedido a la *Mesa {pedido.numero_mesa}* ahora!"
        else:
            texto_entrega = "¡Ya podés venir a retirar tu pedido por la barra principal!"

        texto = (
            f"🇸🇱 *BUFFET SAN MARTÍN* 🇸🇱\n\n"
            f"¡Tu pedido *#{pedido.id}* está LISTO! 🚀🍔\n\n"
            f"🗣️ {nombre_limpio},\n"
            f"*{texto_entrega}*\n\n"
            f"¡Que lo disfrutes! 🍽️🥤"
        )
        return _enviar_mensaje_green_api(pedido.telefono_cliente, texto)
    except Exception as e:
        print(f"Error Whatsapp (Pedido Listo): {e}")


def notificar_pedido_cancelado(pedido_id):
    try:
        pedido = Pedido.objects.get(id=pedido_id)
        nombre_limpio = pedido.nombre_cliente.split(" (Nota:")[0] if pedido.nombre_cliente else "Cliente"
        texto = (
            f"🇸🇱 *BUFFET SAN MARTÍN* 🇸🇱\n\n"
            f"Hola {nombre_limpio}.\n"
            f"Lamentablemente tu pedido *#{pedido.id}* ha sido cancelado ❌.\n\n"
            f"Si hubo algún problema o fue un error, por favor acercate al mostrador del buffet. 🙏"
        )
        return _enviar_mensaje_green_api(pedido.telefono_cliente, texto)
    except Exception as e:
        print(f"Error Whatsapp (Cancelado): {e}")