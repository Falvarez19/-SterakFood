import os
import time
import requests
import winsound
import textwrap
import re
import threading 
from datetime import datetime
from escpos.printer import Win32Raw, Network 
from PIL import Image, ImageDraw 
import pystray 

BASE_URL = os.environ.get("TICKETERA_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
URL_PENDIENTES = f"{BASE_URL}/api/pedidos-pendientes/"
URL_MARCAR = f"{BASE_URL}/api/marcar-impreso/"
URL_TICKETS_CUENTA = f"{BASE_URL}/api/tickets-cuenta-pendientes/"
URL_MARCAR_CUENTA = f"{BASE_URL}/api/marcar-ticket-cuenta-impreso/"
TICKETERA_PRINT_TOKEN = os.environ.get('TICKETERA_PRINT_TOKEN', '').strip()
URL_FACTURAS = f'{BASE_URL}/api/tickets-fiscales-pendientes/'
URL_FACTURAS_CONFIRMAR = f'{BASE_URL}/api/tickets-fiscales-confirmar/'

NOMBRE_RESTAURANTE = os.environ.get("RESTAURANT_NAME", "SterakFood").strip() or "SterakFood"
IMPRESORA_CAJA = os.environ.get("IMPRESORA_CAJA", "FACTURA_PYTHON")
IP_COCINA = os.environ.get("IP_COCINA", "192.168.1.100")
IP_BARRA = os.environ.get("IP_BARRA", "192.168.1.101")
ANCHO_TICKET = int(os.environ.get("ANCHO_TICKET", "32")) 

# Variable global para prender/apagar
sistema_activo = True

def hacer_ruido():
    for _ in range(3):
        winsound.Beep(2500, 300)
        time.sleep(0.1)

def _texto_cocina_sin_importe(texto):
    """Protección extra para el agente: no imprime suplementos económicos en comandas."""
    return re.sub(r'\s*\(\s*[+-]\s*\$?\s*\d+(?:[.,]\d{1,2})?\s*\)', '',
                  str(texto or '')).strip()


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
    if entrega == 'para_llevar':
        impresora.text("*** PARA LLEVAR ***\n")
        impresora.text(f"PEDIDO #{pedido.get('id', '')}\n")
    elif entrega == 'mesa':
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
    if pedido.get('alerta_celiaco') or any(i.get('aviso_celiaco') for i in items):
        impresora.set(align='center', font='a', bold=True, double_height=True)
        impresora.text('*** ALERTA CELIAQUIA ***\n')
        impresora.set(align='left', font='a', bold=True, double_height=False)
        for aviso in ('REVISAR INGREDIENTES APTOS', 'EVITAR CONTAMINACION CRUZADA',
                      'CONFIRMAR CON COCINA ANTES DE PREPARAR'):
            for linea in textwrap.wrap(aviso, width=ANCHO_TICKET):
                impresora.text(linea+'\n')
        impresora.text("-" * ANCHO_TICKET + "\n")
    
    if entrega == 'para_llevar' and pedido.get('notas'):
        impresora.set(align='left', font='a', bold=True)
        impresora.text("INDICACIONES:\n")
        for linea in textwrap.wrap(str(pedido['notas']), width=ANCHO_TICKET):
            impresora.text(f"{linea}\n")
        impresora.text("-" * ANCHO_TICKET + "\n")
    for item in items:
        nombre_crudo = str(item.get('nombre') or 'Producto')
        plato_principal = str(item.get('plato') or '').strip()
        opciones = item.get('opciones')
        if plato_principal and isinstance(opciones, list):
            # Estructura explícita: conserva las variantes con (+precio) y
            # nombres que contienen paréntesis, sin truncar las indicaciones.
            lista_opciones = [_texto_cocina_sin_importe(op) for op in opciones if str(op).strip()]
        elif ' (' in nombre_crudo and nombre_crudo.endswith(')'):
            # Compatibilidad con agentes/servidores antiguos.
            plato_principal, resto = nombre_crudo.split(' (', 1)
            lista_opciones = [_texto_cocina_sin_importe(op) for op in resto.rsplit(')', 1)[0].split(' | ')]
        else:
            plato_principal = nombre_crudo
            lista_opciones = []
        plato_principal = _texto_cocina_sin_importe(plato_principal)
        impresora.set(align='left', font='a', bold=True)
        if item.get('aviso_celiaco'):
            impresora.text('!!! CELIACO - REVISAR !!!\n')
        for linea in textwrap.wrap(f"{item['cantidad']}x {plato_principal}", width=ANCHO_TICKET):
            impresora.text(f"{linea}\n")
        if lista_opciones:
            impresora.set(align='left', font='b', bold=False)
            for opcion in lista_opciones:
                for op_linea in textwrap.wrap(f"   -> {opcion}", width=42):
                    impresora.text(f"{op_linea}\n")

    if "FALTA PAGAR" in pedido.get('pago', '') or "NO PAGADO" in pedido.get('pago', ''):
        impresora.text("-" * ANCHO_TICKET + "\n")
        impresora.set(align='center', font='a', bold=True)
        impresora.text("PEDIDO PENDIENTE DE COBRO\n" if entrega == 'para_llevar' else "EFECTIVO - FALTA PAGAR\n")

    impresora.set(align='left', font='a', bold=False)
    impresora.text("-" * ANCHO_TICKET + "\n\n\n\n")
    impresora.cut()

def imprimir_ticket_cobro(impresora, pedido):
    impresora.text('\x1b\x40') 
    impresora.set(align='center', font='a', bold=False, double_height=False, double_width=False)
    
    impresora.set(bold=True)
    impresora.text(NOMBRE_RESTAURANTE.upper() + "\n")
    impresora.set(bold=False)
    
    fecha_str = datetime.now().strftime("%d/%m/%y %H:%M")
    impresora.text(f"{fecha_str} | Pedido #{pedido.get('id', '')}\n")
    mozo = pedido.get('mozo') or 'CAJA'
    impresora.text(f"MESA: {pedido.get('mesa', '?')} | MOZO: {mozo}\n")
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



# Comprobante no fiscal. Este camino no toca ventas, caja ni saldo contable.
def imprimir_ticket_deuda(impresora, comprobante):
    def moneda(numero):
        try: return '$ ' + f'{float(numero):.2f}'
        except (TypeError, ValueError): return '$ 0.00'

    def linea_etiqueta(etiqueta, numero):
        valor = moneda(numero)
        espacio = max(1, ANCHO_TICKET - len(etiqueta) - len(valor))
        impresora.text(etiqueta + ' ' * espacio + valor + '\n')

    impresora.text('\x1b\x40')
    impresora.set(align='center', font='a', bold=True, double_height=False, double_width=False)
    impresora.text(NOMBRE_RESTAURANTE.upper() + '\n')
    estado = comprobante.get('tipo') == 'estado'
    impresora.text(('ESTADO DE CUENTA' if estado else 'COMPROBANTE CUENTA CORRIENTE') + '\n')
    impresora.set(bold=False)
    impresora.text(str(comprobante.get('fecha', '')) + '\n')
    impresora.text('COMPROBANTE NO FISCAL\n')
    impresora.text('-' * ANCHO_TICKET + '\n')
    for linea in textwrap.wrap('CLIENTE: ' + str(comprobante.get('cliente', '')), width=ANCHO_TICKET):
        impresora.text(linea + '\n')
    if comprobante.get('mesa'):
        impresora.text('MESA: ' + str(comprobante['mesa'])[:12] + '\n')
    if comprobante.get('mozo'):
        for linea in textwrap.wrap('MOZO: ' + str(comprobante['mozo']), width=ANCHO_TICKET):
            impresora.text(linea + '\n')
    impresora.text('-' * ANCHO_TICKET + '\n')
    if estado: impresora.text('ULTIMOS MOVIMIENTOS\n')
    else: impresora.text('DETALLE DEL CONSUMO\n')
    for item in comprobante.get('items', []):
        cant = str(item.get('cantidad', 1))
        nombre = str(item.get('nombre', ''))
        importe = moneda(item.get('subtotal', 0))
        for linea in textwrap.wrap(cant + 'x ' + nombre, width=ANCHO_TICKET) or ['']:
            impresora.text(linea + '\n')
        impresora.set(align='right',bold=False)
        impresora.text(importe + '\n')
        impresora.set(align='left', bold=False)
    impresora.text('-' * ANCHO_TICKET + '\n')
    if not estado:
        impresora.set(bold=True)
        linea_etiqueta('CONSUMO A CUENTA:', comprobante.get('total', 0))
        impresora.set(bold=False)
        anterior = float(comprobante.get('saldo_anterior') or 0)
        if anterior >= 0:
            linea_etiqueta('A FAVOR ANTES:', anterior)
        else:
            linea_etiqueta('DEUDA ANTERIOR:', -anterior)
    saldo = float(comprobante.get('saldo_posterior') or 0)
    impresora.set(bold=True)
    if saldo > 0: linea_etiqueta('SALDO A FAVOR:', saldo)
    elif saldo < 0: linea_etiqueta('DEUDA TOTAL:', -saldo)
    else: impresora.text('SALDO AL DIA: $ 0.00\n')
    impresora.set(align='center', bold=False)
    impresora.text('-' * ANCHO_TICKET + '\n')
    impresora.text('NO VALIDO COMO FACTURA\n')
    impresora.text('Documento informativo\n\n\n')
    impresora.cut()


def imprimir_pendientes_cuenta():
    cabeceras = {'X-Ticketera-Token': TICKETERA_PRINT_TOKEN} if TICKETERA_PRINT_TOKEN else {}
    respuesta = requests.get(URL_TICKETS_CUENTA, headers=cabeceras, timeout=10)
    respuesta.raise_for_status()
    datos = respuesta.json()
    for comprobante in datos.get('tickets', []):
        try:
            imp_caja = Win32Raw(IMPRESORA_CAJA)
            try:
                imprimir_ticket_deuda(imp_caja, comprobante)
            finally:
                imp_caja.close()
            confirmado = requests.post(
                f"{URL_MARCAR_CUENTA}{comprobante['id']}/",
                headers=cabeceras, timeout=10,
            )
            confirmado.raise_for_status()
        except Exception as error:
            # Si falla la impresora, NO marcar impreso: queda en cola.
            print(f'Error imprimiendo ticket de deuda: {error}')


# Facturas fiscales: mismo destino Win32Raw de caja, diferente cola. Solo
# imprime comprobantes con CAE confirmado por ARCA en el servidor.
def imprimir_factura_fiscal(impresora, factura):
    import qrcode
    entorno = factura.get('entorno')
    prueba = entorno != 'produccion'
    impresora.text('\x1b\x40')
    impresora.set(align='center',font='a',bold=True)
    impresora.text(str(factura.get('razon_social') or NOMBRE_RESTAURANTE).upper()+'\n')
    if prueba:
        impresora.text('HOMOLOGACION - SIN VALOR FISCAL\n')
    if factura.get('domicilio'):
        for l in textwrap.wrap(str(factura['domicilio']),width=ANCHO_TICKET): impresora.text(l+'\n')
    impresora.text('CUIT '+str(factura['cuit'])+'\n')
    for campo,etiqueta in [('condicion_iva_emisor','IVA: '),('ingresos_brutos','IIBB: '),('inicio_actividades','Inicio actividades: ')]:
        if factura.get(campo):
            for l in textwrap.wrap(etiqueta+str(factura[campo]),width=ANCHO_TICKET): impresora.text(l+'\n')
    impresora.text('FACTURA B\n')
    impresora.text('Nro. '+str(factura['numero'])+'\n')
    fecha = str(factura.get('fecha',''))
    if len(fecha)==8: fecha=f'{fecha[6:8]}/{fecha[4:6]}/{fecha[:4]}'
    impresora.text('Fecha: '+fecha+'\n')
    impresora.set(align='left',bold=False)
    impresora.text('-'*ANCHO_TICKET+'\n')
    impresora.text('Consumidor Final\n')
    impresora.text('Mesa '+str(factura.get('mesa',''))+'  Mozo '+str(factura.get('mozo',''))+'\n')
    impresora.text('-'*ANCHO_TICKET+'\n')
    for item in factura.get('items',[]):
        nombre=str(item.get('nombre','Producto')).upper()
        cantidad=int(item.get('cantidad',1)); subtotal=str(item.get('subtotal','0'))
        for l in textwrap.wrap(f'{cantidad}x {nombre}',width=ANCHO_TICKET): impresora.text(l+'\n')
        impresora.set(align='right');impresora.text('$ '+subtotal+'\n')
        impresora.set(align='left')
    impresora.text('-'*ANCHO_TICKET+'\n')
    impresora.set(align='right',bold=True)
    impresora.text('TOTAL $ '+str(factura['total'])+'\n')
    impresora.set(align='center',bold=False)
    impresora.text('CAE: '+str(factura['cae'])+'\n')
    venc=str(factura.get('vencimiento_cae',''))
    if len(venc)==8: venc=f'{venc[6:8]}/{venc[4:6]}/{venc[:4]}'
    impresora.text('Vto. CAE: '+venc+'\n')
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=4,border=2)
    qr.add_data(factura['url_qr']);qr.make(fit=True)
    impresora.image(qr.make_image(fill_color='black',back_color='white').convert('RGB'))
    if prueba: impresora.text('COMPROBANTE DE PRUEBA\n')
    impresora.text('\n\n\n')
    impresora.cut()


def imprimir_pendientes_fiscales():
    if not TICKETERA_PRINT_TOKEN:
        return   # No consultar cola fiscal sin token configurado.
    headers={'X-Ticketera-Token':TICKETERA_PRINT_TOKEN}
    respuesta=requests.get(URL_FACTURAS,headers=headers,timeout=10)
    respuesta.raise_for_status()
    for factura in respuesta.json().get('tickets',[]):
        try:
            impresora=Win32Raw(IMPRESORA_CAJA)
            try: imprimir_factura_fiscal(impresora,factura)
            finally: impresora.close()
            # ACK después de imprimir; si se pierde ACK podría reimprimirse.
            ack=requests.post(f"{URL_FACTURAS_CONFIRMAR}{factura['id']}/",headers=headers,timeout=10)
            ack.raise_for_status()
        except Exception as exc:
            print(f'Error imprimiendo factura fiscal #{factura.get("id")}: {exc}')

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
                        impresa_cocina = True

                        # 🔥 IMPRIME EN COCINA (AHORA SÍ VA POR RED A LA IP) 🔥
                        if len(pedido.get('items_cocina', [])) > 0:
                            try:
                                imp_cocina = Network(IP_COCINA) # Acá estaba el error, ya está arreglado
                                imprimir_ticket(imp_cocina, pedido, "COCINA", pedido['items_cocina'])
                                imp_cocina.close()
                            except Exception as e:
                                impresa_cocina = False
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

                        if pedido.get('entrega', '').lower() == 'para_llevar' and not impresa_cocina:
                            # No perder una comanda para llevar si no se pudo imprimir.
                            # ATENCIÓN: corte de red entre impresión y confirmación puede causar duplicados.
                            continue
                        requests.post(f"{URL_MARCAR}{pedido['id']}/", timeout=10)
        except Exception: 
            pass
        try:
            imprimir_pendientes_cuenta()
        except Exception as error:
            print(f'No se pudo consultar cola de comprobantes: {error}')
        try:
            imprimir_pendientes_fiscales()
        except Exception as error:
            print(f'No se pudo consultar cola fiscal: {error}')
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
    
    icono = pystray.Icon("ticketera", crear_imagen_icono(), "Ticketera SterakFood", menu)
    
    hilo = threading.Thread(target=bucle_impresion, daemon=True)
    hilo.start()
    
    icono.run()

if __name__ == "__main__":
    iniciar_tray()