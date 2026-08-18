🍔 **SterakFood - Sistema de Pedidos y Gestión**
Sistema integral de gestión gastronómica desarrollado para optimizar la toma de pedidos, el procesamiento de pagos y la comunicación directa con cocina y barra mediante hardware dedicado.

🔗 **Acceso al Proyecto**
Podés ver el sistema funcionando en tiempo real acá:
👉 https://github.com/Falvarez19/-SterakFood.git

Nota: Al ser una PWA, podés abrir este link desde tu celular, tocar los tres puntitos del navegador y seleccionar "Instalar aplicación" para tenerlo como un acceso directo en tu pantalla de inicio.

🚀 **Características Principales**
* **Arquitectura Híbrida:** Combina un backend en Django (gestión de nube) con un agente local en Python que gestiona la impresión física.
* **Progressive Web App (PWA):** Interfaz móvil instalable, responsive y optimizada.
* **Lógica de Descuentos Inteligente:** Aplicación automática de un 10% OFF en efectivo los fines de semana (Sáb/Dom) de 12:00 a 15:00 hs.
* **Gestión de Hardware (Ticketeras):** Microservicio propio (`ticketera.py`) que rutea comandas a Cocina (IP), Barra (IP) y Caja (USB) en tiempo real.
* **Integración Fintech:** Procesamiento de pagos vía MercadoPago con Webhooks automáticos.
* **Panel de Control Pro:** Tablero administrativo avanzado con actualización en tiempo real (AJAX), control de stock/precios dinámicos, **Cierre de Caja detallado y segmentado por cada mostrador** con desglose de productos vendidos, y la funcionalidad de **Reinicio Automático del Contador de Pedidos** al cerrar turno.

🏗️ **Arquitectura Técnica**
El sistema se divide en dos capas de software:

**Backend (Django):**
* **Motor de Carrito:** Basado en sesiones, permite configurar opciones personalizadas (guarniciones, puntos de cocción) mediante llaves dinámicas.
* **Optimización:** Uso de `select_related` para reducir consultas a la base de datos y mejorar la carga en móviles.
* **Seguridad:** Panel administrativo con acceso restringido mediante PIN y sesiones de expiración inmediata al cerrar el navegador.

**Agente Local (Python Agent):**
* **Escucha en Segundo Plano:** El agente consulta la API de Django cada 5 segundos.
* **Routing:** Diferencia entre impresoras USB (`Win32Raw`) e impresoras de red (`Network`) según el puesto de venta.
* **Renderizado Térmico:** Motor matemático propio que alinea textos y precios en tickets de 58mm (32 caracteres de ancho) sin utilizar librerías de terceros complejas para el diseño.

⚙️ **Instalación y Despliegue**
**1. Backend (Django)**
* Clonar: `git clone https://github.com/Falvarez19/-SterakFood.git`
* Instalar dependencias: `pip install -r requirements.txt`
* Migrar: `python manage.py makemigrations && python manage.py migrate`
* Correr: `python manage.py runserver`

**2. Agente Local (Ticketera)**
Para el funcionamiento de las impresoras:
* Instalar librerías: `pip install pystray pillow requests escpos`
* El script `ticketera.py` debe estar en la PC de caja.
* Ejecutar mediante `iniciar_ticketera.bat` (configurado como proceso oculto para iniciar con Windows).

🗄️ **Modelos de Datos Clave**
* **Pedido:** Registra el flujo financiero, el método de pago, el estado y el estado de impresión (`impreso_caja`).
* **DetallePedido:** "Fotografía" del pedido (precio congelado al momento de la compra + extras elegidos).
* **Configuracion:** Permite activar/desactivar el buffet globalmente mediante un "Interruptor Maestro" en el panel.

🛠️ **Tecnologías**
* **Backend:** Python / Django.
* **Frontend:** JS Vanilla / HTML5 / CSS3 (Con diseño adaptativo claro/oscuro y componentes visuales modernos estilo SaaS).
* **Hardware:** `python-escpos` para comunicación con ticketeras.
* **Infraestructura:** Render.com (Nube).

Desarrollado para **SterakFood**. Optimizado para alta demanda y operaciones gastronómicas en tiempo real.
