# -SterakFood
Sistema integral de gestión gastronómica desarrollado para optimizar la toma de pedidos, el procesamiento de pagos y la comunicación directa con cocina y barra mediante hardware dedicado.

🍔 **SterakFood - Sistema de Pedidos y Gestión**[cite: 2]
Sistema integral de gestión gastronómica desarrollado para optimizar la toma de pedidos, el procesamiento de pagos y la comunicación directa con cocina y barra mediante hardware dedicado[cite: 2].

🔗 **Acceso al Proyecto**
Podés ver el sistema funcionando en tiempo real acá:
👉 https://github.com/Falvarez19/-SterakFood.git

Nota: Al ser una PWA, podés abrir este link desde tu celular, tocar los tres puntitos del navegador y seleccionar "Instalar aplicación" para tenerlo como un acceso directo en tu pantalla de inicio[cite: 2].

🚀 **Características Principales**
* **Arquitectura Híbrida:** Combina un backend en Django (gestión de nube) con un agente local en Python que gestiona la impresión física[cite: 2].
* **Progressive Web App (PWA):** Interfaz móvil instalable, responsive y optimizada[cite: 2].
* **Lógica de Descuentos Inteligente:** Aplicación automática de un 10% OFF en efectivo los fines de semana (Sáb/Dom) de 12:00 a 15:00 hs[cite: 2].
* **Gestión de Hardware (Ticketeras):** Microservicio propio (`ticketera.py`) que rutea comandas a Cocina (IP), Barra (IP) y Caja (USB) en tiempo real[cite: 2].
* **Integración Fintech:** Procesamiento de pagos vía MercadoPago con Webhooks automáticos[cite: 2].
* **Panel de Control Pro:** Tablero administrativo avanzado con actualización en tiempo real (AJAX), control de stock/precios dinámicos, **Cierre de Caja detallado y segmentado por cada mostrador** con desglose de productos vendidos, y la funcionalidad de **Reinicio Automático del Contador de Pedidos** al cerrar turno.

🏗️ **Arquitectura Técnica**
El sistema se divide en dos capas de software[cite: 2]:

**Backend (Django)[cite: 2]:**
* **Motor de Carrito:** Basado en sesiones, permite configurar opciones personalizadas (guarniciones, puntos de cocción) mediante llaves dinámicas[cite: 2].
* **Optimización:** Uso de `select_related` para reducir consultas a la base de datos y mejorar la carga en móviles[cite: 2].
* **Seguridad:** Panel administrativo con acceso restringido mediante PIN y sesiones de expiración inmediata al cerrar el navegador[cite: 2].

**Agente Local (Python Agent)[cite: 2]:**
* **Escucha en Segundo Plano:** El agente consulta la API de Django cada 5 segundos[cite: 2].
* **Routing:** Diferencia entre impresoras USB (`Win32Raw`) e impresoras de red (`Network`) según el puesto de venta[cite: 2].
* **Renderizado Térmico:** Motor matemático propio que alinea textos y precios en tickets de 58mm (32 caracteres de ancho) sin utilizar librerías de terceros complejas para el diseño[cite: 2].

⚙️ **Instalación y Despliegue**
**1. Backend (Django)[cite: 2]**
* Clonar: `git clone https://github.com/Falvarez19/-SterakFood.git`
* Instalar dependencias: `pip install -r requirements.txt`[cite: 2]
* Migrar: `python manage.py makemigrations && python manage.py migrate`[cite: 2]
* Correr: `python manage.py runserver`[cite: 2]

**2. Agente Local (Ticketera)[cite: 2]**
Para el funcionamiento de las impresoras[cite: 2]:
* Instalar librerías: `pip install pystray pillow requests escpos`[cite: 2]
* El script `ticketera.py` debe estar en la PC de caja[cite: 2].
* Ejecutar mediante `iniciar_ticketera.bat` (configurado como proceso oculto para iniciar con Windows)[cite: 2].

🗄️ **Modelos de Datos Clave**
* **Pedido:** Registra el flujo financiero, el método de pago, el estado y el estado de impresión (`impreso_caja`)[cite: 2].
* **DetallePedido:** "Fotografía" del pedido (precio congelado al momento de la compra + extras elegidos)[cite: 2].
* **Configuracion:** Permite activar/desactivar el buffet globalmente mediante un "Interruptor Maestro" en el panel[cite: 2].

🛠️ **Tecnologías**
* **Backend:** Python / Django[cite: 2].
* **Frontend:** JS Vanilla / HTML5 / CSS3 (Con diseño adaptativo claro/oscuro y componentes visuales modernos estilo SaaS)[cite: 2].
* **Hardware:** `python-escpos` para comunicación con ticketeras[cite: 2].
* **Infraestructura:** Render.com (Nube)[cite: 2].

Desarrollado para **SterakFood**. Optimizado para alta demanda y operaciones gastronómicas en tiempo real[cite: 2].
