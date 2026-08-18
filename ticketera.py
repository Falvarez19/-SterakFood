import time
import requests
import winsound
import textwrap 
import threading 
from datetime import datetime
from escpos.printer import Win32Raw, Network 
from PIL import Image, ImageDraw 
import pystray 

URL_PENDIENTES = "https://buffetclubsm.com.ar/api/pedidos-pendientes/"
URL_MARCAR = "https://buffetclubsm.com.ar/api/marcar-impreso/"

IMPRESORA_CAJA = "FACTURA_PYTHON"
IP_COCINA      = "192.168.200.250" # IP de la cocina
IP_BARRA       = "192.168.200.198" # IP de la barra
ANCHO_TICKET = 32 

# Variable global para prender/apagar
sistema_activo = True

def hacer_ruido():
    for _ in range(3):
        winsound.Beep(2500, 300)
        time.sleep(0.1)

def imprimir_ticket(impresora, pedido, tipo_ticket, items):
    impresora.text('\x1b\x40') 
    impresora.set(align='center', font='a', bold=True, double_height=True, double_width=False)
    impresora.text(f"--- {tipo_ticket} ---\n")
    impresora.set(align='center', font='a', bold=True, double_height=False, double_width=False)
    impresora.text(f"Hora: {pedido.get('hora', '')} hs\n")
    impresora.set(bold=False)
    impresora.text("-" * ANCHO_TICKET + "\n")
    
    entrega = str(pedido.get('entrega', '')).lower()
    cliente = str(pedido.get('cliente', '')).upper()
    
    impresora.set(align='center', font='a', bold=True)
    if entrega == 'mesa':
        impresora.text("LLEVAR A:\n")
        impresora.set(align='center', bold=True, double_height=True, double_width=False)
        impresora.text(f"MESA {pedido.get('mesa', '?')}\n")
    else:
        impresora.text("RETIRO POR MOSTRADOR\n")
        
    impresora.set(align='center', bold=True, double_height=False, double_width=False)
    for linea in textwrap.wrap(cliente, width=ANCHO_TICKET):
        impresora.text(f"{linea}\n")
    
    impresora.set(align='left', font='a', bold=False)
    impresora.text("-" * ANCHO_TICKET + "\n")
    
    for item in items:
        nombre_crudo = item['nombre']
        if "(" in nombre_crudo and ")" in nombre_crudo:
            partes = nombre_crudo.split("(")
            plato_principal = partes[0].strip()
            opciones_texto = partes[1].replace(")", "").strip()
            
            impresora.set(align='left', font='a', bold=True)
            for linea in textwrap.wrap(f"{item['cantidad']}x {plato_principal}", width=ANCHO_TICKET):
                impresora.text(f"{linea}\n")
            
            impresora.set(align='left', font='b', bold=False)
            lista_opciones = opciones_texto.split(" | ")
            for opcion in lista_opciones:
                for op_linea in textwrap.wrap(f"   -> {opcion}", width=42): 
                    impresora.text(f"{op_linea}\n")
        else:
            impresora.set(align='left', font='a', bold=True)
            for linea in textwrap.wrap(f"{item['cantidad']}x {nombre_crudo}", width=ANCHO_TICKET):
                impresora.text(f"{linea}\n")
    
    if "FALTA PAGAR" in pedido.get('pago', '') or "NO PAGADO" in pedido.get('pago', ''):
        impresora.text("-" * ANCHO_TICKET + "\n")
        impresora.set(align='center', font='a', bold=True)
        impresora.text("EFECTIVO - FALTA PAGAR\n")

    impresora.set(align='left', font='a', bold=False)
    impresora.text("-" * ANCHO_TICKET + "\n\n\n\n")
    impresora.cut()

def imprimir_ticket_cobro(impresora, pedido):
    impresora.text('\x1b\x40') 
    impresora.set(align='center', font='a', bold=False, double_height=False, double_width=False)
    
    impresora.set(bold=True)
    impresora.text("BUFFET SAN MARTIN\n")
    impresora.set(bold=False)
    
    fecha_str = datetime.now().strftime("%d/%m/%y %H:%M")
    impresora.text(f"{fecha_str} | Pedido #{pedido.get('id', '')}\n")
    impresora.text(f"MESA: {pedido.get('mesa', '?')} | MOZO: CAJA\n")
    impresora.text("-" * ANCHO_TICKET + "\n")
    
    impresora.set(align='left', bold=True)
    impresora.text("Cant Detalle             Importe\n")
    impresora.set(bold=False)
    impresora.text("-" * ANCHO_TICKET + "\n")
    
    items = pedido.get('items_caja', [])
    for item in items:
        desc = item['descripcion'] 
        if "x " in desc:
            partes = desc.split("x ", 1)
            cant_str = partes[0].strip()
            detalle_str = partes[1].strip().upper()
        else:
            cant_str = "1"
            detalle_str = desc.upper()
            
        try:
            cant_float = float(cant_str)
            cant_format = f"{cant_float:.0f}" if cant_float.is_integer() else f"{cant_float:.1f}"
        except:
            cant_format = cant_str[:3]
            
        importe_num = item['subtotal'].replace('$', '').replace(',', '').strip()
        try: importe_str = f"{float(importe_num):.2f}"
        except: importe_str = importe_num
            
        len_importe = len(importe_str)
        espacio_detalle = ANCHO_TICKET - 4 - 1 - len_importe - 1
        
        if len(detalle_str) > espacio_detalle:
            lineas_detalle = textwrap.wrap(detalle_str, width=espacio_detalle)
            impresora.text(f"{cant_format:<4} {lineas_detalle[0].ljust(espacio_detalle)} {importe_str:>{len_importe}}\n")
            for l in lineas_detalle[1:]:
                impresora.text(f"     {l}\n") 
        else:
            impresora.text(f"{cant_format:<4} {detalle_str.ljust(espacio_detalle)} {importe_str:>{len_importe}}\n")
            
    impresora.text("-" * ANCHO_TICKET + "\n")
    
    total_str = str(pedido.get('total', '0')).replace('$', '').replace(',', '.')
    try: total_float = float(total_str)
    except: total_float = 0.0
        
    # 🔥 LÓGICA DE DESCUENTO 10% EFECTIVO (Sábado/Domingo 12-15hs) 🔥
    es_efectivo = "EFECTIVO" in str(pedido.get('pago', '')).upper()
    ahora = datetime.now()
    es_finde = ahora.weekday() in [5, 6]
    es_horario = 12 <= ahora.hour < 15
    
    if es_efectivo and es_finde and es_horario:
        descuento = total_float * 0.10
        total_final = total_float - descuento
        
        impresora.set(align='right', bold=False)
        impresora.text(f"SUBTOTAL: $ {total_float:.2f}\n")
        impresora.text(f"DESC. 10% EFECTIVO: -$ {descuento:.2f}\n")
        impresora.set(bold=True)
        impresora.text(f"TOTAL A PAGAR: $ {total_final:.2f}\n")
    else:
        impresora.set(align='right', bold=True)
        impresora.text(f"TOTAL: $ {total_float:.2f}\n")
    
    impresora.set(align='center', bold=False)
    impresora.text("-" * ANCHO_TICKET + "\n")
    impresora.text("NO VALIDO COMO FACTURA\n")
    impresora.text("\n\n\n\n")
    impresora.cut()

# ====================================================================
# 🔥 BUCLE QUE CORRE EN SEGUNDO PLANO 🔥
# ====================================================================
def bucle_impresion():
    global sistema_activo
    while sistema_activo:
        try:
            res = requests.get(URL_PENDIENTES, timeout=10)
            if res.status_code == 200:
                datos = res.json()
                if datos.get('status') == 'ok' and datos.get('pedidos'):
                    for pedido in datos['pedidos']:
                        hacer_ruido()
                        
                        # 🔥 IMPRIME EN COCINA (AHORA SÍ VA POR RED A LA IP) 🔥
                        if len(pedido.get('items_cocina', [])) > 0:
                            try:
                                imp_cocina = Network(IP_COCINA) # Acá estaba el error, ya está arreglado
                                imprimir_ticket(imp_cocina, pedido, "COCINA", pedido['items_cocina'])
                                imp_cocina.close()
                            except Exception as e: 
                                print(f"Error en cocina: {e}")
                                
                        # 🔥 IMPRIME EN BARRA (Va por RED a la IP de la barra) 🔥
                        if len(pedido.get('items_barra', [])) > 0:
                            try:
                                imp_barra = Network(IP_BARRA)
                                imprimir_ticket(imp_barra, pedido, "BARRA / CAFE", pedido['items_barra'])
                                imp_barra.close()
                            except Exception as e: 
                                print(f"Error en barra: {e}")
                                
                        # IMPRIME LA CUENTA EN LA CAJA (Sigue en USB)
                        if pedido.get('imprimir_ticket_cobro'):
                            try:
                                imp_caja = Win32Raw(IMPRESORA_CAJA)
                                imprimir_ticket_cobro(imp_caja, pedido)
                                imp_caja.close()
                            except Exception as e: 
                                print(f"Error en caja: {e}")

                        requests.post(f"{URL_MARCAR}{pedido['id']}/", timeout=10)
        except Exception: 
            pass
        time.sleep(5)

# ====================================================================
# 🔥 DIBUJO Y MENÚ DEL RELOJ 🔥
# ====================================================================
def crear_imagen_icono():
    image = Image.new('RGB', (64, 64), color='#103b70')
    dc = ImageDraw.Draw(image)
    dc.ellipse([(16, 16), (48, 48)], fill='#d4a373')
    return image

def apagar_sistema(icon, item):
    global sistema_activo
    sistema_activo = False
    icon.stop()

def iniciar_tray():
    menu = pystray.Menu(
        pystray.MenuItem('✅ Ticketera Activa', lambda: None, enabled=False),
        pystray.MenuItem('❌ Apagar Ticketera', apagar_sistema)
    )
    
    icono = pystray.Icon("ticketera", crear_imagen_icono(), "Ticketera Buffet SM", menu)
    
    hilo = threading.Thread(target=bucle_impresion, daemon=True)
    hilo.start()
    
    icono.run()

if __name__ == "__main__":
    iniciar_tray()