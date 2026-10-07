# SterakFood — Guía para crear un restaurante nuevo

Esta carpeta es la **maqueta principal**. La idea es duplicarla para cada restaurante y cambiar solamente identidad, datos del negocio, pagos, dominio e impresoras, sin tocar la lógica central.

> Regla recomendada: nunca trabajes directamente sobre esta maqueta. Copiá la carpeta, renombrá la copia y hacé los cambios del nuevo restaurante ahí.

---

## 1. Copiar la maqueta

Ejemplo:

```text
SterakFood_Maqueta_Principal/
↓ copiar
Restaurante_La_Esquina/
```

Después creá un entorno virtual nuevo y ejecutá:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py check
python manage.py runserver
```

No borres las migraciones existentes.

---

## 2. Nombre del restaurante

Buscá y reemplazá estas palabras en el proyecto:

```text
SterakFood
Sterak Food
STERAKFOOD
```

Los lugares más importantes son:

```text
pedidos/templates/pedidos/base.html
pedidos/templates/pedidos/inicio.html
pedidos/templates/pedidos/panel.html
pedidos/templates/pedidos/salon.html
pedidos/templates/pedidos/cerrado.html
pedidos/templates/pedidos/404.html
pedidos/templates/pedidos/seguimiento.html
pedidos/templates/manifest.json
README.md
```

También configurá en producción:

```text
RESTAURANT_NAME=Nombre del Restaurante
```

`ticketera.py` usa esa variable para imprimir el nombre automáticamente.

---

## 3. Logo, fondo e imágenes

Reemplazá los archivos manteniendo los mismos nombres para no tener que tocar HTML:

```text
pedidos/static/img/logo.png
pedidos/static/img/logo-modo.png
pedidos/static/img/fondo-buffet.png
```

### Modal de bienvenida

Si querés que aparezca una tarjeta al entrar al menú, guardala como:

```text
pedidos/static/img/bienvenida_buffet.webp
```

y activá:

```text
WELCOME_MODAL_ENABLED=true
```

Si no existe una tarjeta personalizada, dejá:

```text
WELCOME_MODAL_ENABLED=false
```

El modal ya está programado para mostrarse una vez por sesión y cerrarse con la `X`, tocando afuera o con `Escape`.

---

## 4. Colores del restaurante

La paleta principal está al comienzo de:

```text
pedidos/static/css/estilos.css
```

En esta maqueta se usa:

```css
--naranja-sterak
--naranja-brillo
--negro-fondo
--negro-tarjetas
--texto-claro
--texto-mutado
--borde-suave
```

También existen estas variables de compatibilidad porque varios módulos nuevos las usan:

```css
--verde-sanmartin
--dorado-sanmartin
--azul-sanmartin
```

No hace falta renombrarlas para cada restaurante. Lo más seguro es **cambiar solamente los valores de color**.

Ejemplo:

```css
--naranja-sterak: #198754;
--naranja-brillo: #F6C055;

--verde-sanmartin: #198754;
--dorado-sanmartin: #F6C055;
--azul-sanmartin: #103b70;
```

Así no rompés botones, Dashboard, Promos, Salón ni Opiniones.

---

## 5. Dominio y seguridad

Archivo:

```text
SisPedidos/settings.py
```

La maqueta ya acepta variables de entorno.

Configurá:

```text
SECRET_KEY
DEBUG
ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS
DATABASE_URL
```

Ejemplo para Render:

```text
DEBUG=False
ALLOWED_HOSTS=miapp.onrender.com,midominio.com,www.midominio.com
CSRF_TRUSTED_ORIGINS=https://miapp.onrender.com,https://midominio.com,https://www.midominio.com
```

No uses la misma `SECRET_KEY` para todos los restaurantes.

---

## 6. Base de datos

### Desarrollo local

Si `DATABASE_URL` está vacío, usa:

```text
db.sqlite3
```

### Producción

Si existe `DATABASE_URL`, Django usa automáticamente PostgreSQL mediante `dj-database-url`.

Después de copiar la maqueta:

```powershell
python manage.py migrate
```

No uses `loaddata` sobre una base de producción salvo que realmente quieras reemplazar/cargar datos.

---

## 7. Dashboard

El PIN se configura con:

```text
DASHBOARD_PIN
```

Ejemplo:

```text
DASHBOARD_PIN=1234
```

La maqueta mantiene `5968` como acceso de respaldo en el código actual. Si el restaurante va a producción y querés que dependa únicamente del entorno, buscá `5968` en:

```text
pedidos/views.py
```

y eliminá ese PIN fijo.

---

## 8. Puntos de venta / mostradores

Modelo:

```text
PuntoVenta
```

Cada restaurante puede tener sus propios puestos:

```text
Buffet
Kiosco
Parrilla
Foodtruck
Barra
Cafetería
```

Se configuran desde Django Admin/base de datos.

Cada punto tiene:

```text
nombre
slug
telefono
abierto
```

El teléfono se usa para WhatsApp cuando corresponda.

No copies los teléfonos del restaurante anterior.

---

## 9. Categoría especial `Salon`

La categoría:

```text
Salon
```

es **reservada para productos internos del POS**.

Ejemplo:

```text
Gaseosa
Agua
Cubierto
Café interno
```

Los productos de `Salon`:

- aparecen en Salón POS;
- se pueden buscar por código rápido;
- no aparecen en el menú público.

No cambies el nombre `Salon` sin modificar también la lógica en `pedidos/views.py`.

---

## 10. Promociones

Cada producto tiene:

```text
en_promocion
```

Desde Dashboard → Menú podés activar:

```text
🔥 Mostrar en Promos
```

El precio de Promo es el mismo precio normal del producto actualmente.

Si en otro restaurante necesitás un **precio promocional distinto**, habría que agregar un campo nuevo al modelo.

---

## 11. Gestión rápida del menú

El Dashboard incluye:

- búsqueda por nombre/código/categoría;
- filtros por mostrador;
- cambio rápido de precio;
- activar/pausar producto;
- edición completa en modal;
- Promos;
- productos internos `Salon`;
- selector de categorías buscable.

Para cargar muchos productos seguidos:

```text
Dashboard → Nuevo producto
```

al guardar se queda en la misma página con el formulario limpio.

---

## 12. Mozos y mesas

Dashboard → Mesas permite cargar/eliminar mozos.

Salón POS permite:

- escribir el número de mesa y `Enter`;
- tocar una mesa;
- asignar mozo;
- cambiar el mozo de una mesa;
- mantener la cuenta abierta;
- imprimir la cuenta;
- cobrar parcial o completo;
- liberar la mesa al terminar.

Los nombres de los mozos se administran por restaurante. No vienen fijados en código.

---

## 13. Cobros del Salón POS

El Salón POS acepta:

```text
Efectivo
Mercado Pago
Débito
```

Cuando se cobra desde Salón se crea un `Pedido` real y entra al:

```text
Cierre de caja
Historial
Total vendido
Desglose de productos
```

El botón para imprimir una cuenta sin cobrar utiliza un pedido temporal:

```text
ticket_salon_temporal
```

Ese ticket **no entra en el cierre de caja** y se elimina luego de imprimirse.

---

## 14. Opiniones privadas

El menú público puede mostrar una tarjeta:

```text
¿Algo no salió como esperabas?
```

El formulario pide:

```text
Número de mesa
Nombre de la persona
Mozo que lo atendió
Opinión
```

Se guarda en:

```text
OpinionCliente
```

y aparece en:

```text
Dashboard → Opiniones
```

Desde ahí se puede marcar como vista o eliminar.

---

## 15. Reseñas de Google

Para activar la tarjeta:

```text
⭐ Opinar en Google
```

configurá:

```text
GOOGLE_REVIEW_URL=https://...
```

Si la variable queda vacía, la tarjeta de Google **no se muestra**.

Para obtener el enlace correcto:

```text
Google Maps → ficha del negocio → Compartir → Copiar vínculo
```

No reutilices el enlace de otro restaurante.

---

## 16. Mercado Pago

La maqueta lee:

```text
MP_ACCESS_TOKEN
```

Configurá una credencial distinta para cada negocio.

Nunca subas credenciales reales a GitHub.

Revisá también el dominio de retorno y webhook cuando cambies de restaurante.

Rutas actuales:

```text
/webhook-mp/
/exito/<pedido_id>/
```

---

## 17. Nave

La maqueta todavía conserva integración con Nave para el checkout público.

Variable:

```text
NAVE_ACCESS_TOKEN
```

Si un restaurante no usa Nave, podés:

1. dejar la variable vacía;
2. ocultar la opción del checkout;
3. o eliminar la integración más adelante.

Esto **no afecta** al Salón POS, que quedó en Efectivo / Mercado Pago / Débito.

---

## 18. Ticketera e impresoras

Archivo:

```text
ticketera.py
```

Ahora los datos importantes se leen desde variables:

```text
TICKETERA_BASE_URL
RESTAURANT_NAME
IMPRESORA_CAJA
IP_COCINA
IP_BARRA
ANCHO_TICKET
```

Ejemplo:

```text
TICKETERA_BASE_URL=https://mirestaurante.com
RESTAURANT_NAME=Mi Restaurante
IMPRESORA_CAJA=FACTURA_PYTHON
IP_COCINA=192.168.1.250
IP_BARRA=192.168.1.198
ANCHO_TICKET=32
```

Antes de instalar en otro local, revisá físicamente:

- nombre de la impresora USB de caja;
- IP de cocina;
- IP de barra;
- ancho de papel;
- que la PC pueda alcanzar esas IP;
- dominio público correcto.

---

## 19. PWA / aplicación instalable

Archivo:

```text
pedidos/templates/manifest.json
```

Cambiar:

```json
"name"
"short_name"
"description"
"theme_color"
"background_color"
```

Los iconos están en:

```text
pedidos/static/img/
```

Reemplazá los logos antes de entregar el sistema.

También revisá en `base.html`:

```text
<title>
theme-color
apple-mobile-web-app-title
apple-touch-icon
```

---

## 20. WhatsApp

Cada `PuntoVenta` tiene un teléfono.

Revisá también cualquier número fijo o texto de WhatsApp en:

```text
pedidos/views.py
pedidos/whatsapp.py
```

Hacé una búsqueda global por:

```text
telefono
wa.me
whatsapp
```

antes de publicar.

---

## 21. Textos públicos

Antes de entregar un restaurante nuevo, revisar:

```text
pedidos/templates/pedidos/base.html
pedidos/templates/pedidos/inicio.html
pedidos/templates/pedidos/cerrado.html
pedidos/templates/pedidos/exito.html
pedidos/templates/pedidos/seguimiento.html
pedidos/templates/pedidos/404.html
```

Cambiar:

- nombre;
- slogan;
- mensajes de bienvenida;
- horarios;
- textos de descuento;
- datos de retiro;
- mensajes del carrito;
- títulos de navegador.

---

## 22. Horarios y promociones automáticas

Actualmente existe lógica de descuento de efectivo durante ciertos días/horarios.

Buscá:

```text
descuento_activo
es_finde
es_horario
```

en:

```text
pedidos/views.py
ticketera.py
```

Antes de reutilizar la maqueta, decidí si ese restaurante tendrá la misma promoción.

No dejes promociones del cliente anterior sin revisar.

---

## 23. Archivos multimedia en producción

`MEDIA_ROOT` contiene imágenes subidas desde el Dashboard.

En servicios con disco efímero, esas imágenes pueden perderse al redesplegar.

Para producción estable usá:

- disco persistente del hosting; o
- almacenamiento externo de archivos.

El código de Git no reemplaza automáticamente los productos guardados en PostgreSQL.

---

## 24. Qué NO hay que borrar al clonar

No borres:

```text
pedidos/migrations/
pedidos/models.py
pedidos/views.py
pedidos/static/script/script.js
pedidos/static/css/estilos.css
```

Tampoco cambies nombres de campos Django solamente por estética.

Por ejemplo:

```text
en_promocion
codigo_rapido
numero_mesa
tipo_pago
punto_venta
mozo
```

son nombres internos y se deben mantener salvo que hagas una migración planificada.

---

## 25. Qué sí conviene borrar/reiniciar

Para un restaurante totalmente nuevo:

- pedidos viejos;
- productos del restaurante anterior;
- categorías específicas;
- puntos de venta anteriores;
- mozos anteriores;
- opiniones anteriores.

Lo más seguro es empezar con una base nueva y correr:

```powershell
python manage.py migrate
```

en vez de borrar datos a mano de una base ya usada.

---

## 26. Checklist antes de publicar

- [ ] Nombre del restaurante cambiado.
- [ ] Logo nuevo.
- [ ] Fondo nuevo.
- [ ] Colores nuevos.
- [ ] Dominio configurado.
- [ ] `SECRET_KEY` nueva.
- [ ] `DEBUG=False`.
- [ ] `DATABASE_URL` correcta.
- [ ] `ALLOWED_HOSTS` correcto.
- [ ] `CSRF_TRUSTED_ORIGINS` correcto.
- [ ] Mercado Pago correcto.
- [ ] Google Reviews correcto.
- [ ] Modal de bienvenida personalizado o desactivado.
- [ ] Puntos de venta creados.
- [ ] Teléfonos correctos.
- [ ] Mozos cargados.
- [ ] Impresora de caja configurada.
- [ ] IP cocina configurada.
- [ ] IP barra configurada.
- [ ] PWA renombrada.
- [ ] Productos de prueba eliminados.
- [ ] `python manage.py migrate`.
- [ ] `python manage.py check`.
- [ ] Pedido real de prueba.
- [ ] Pago de prueba.
- [ ] Ticket de cocina/barra/caja probado.
- [ ] Cierre de caja probado.
- [ ] Opinión privada probada.
- [ ] Vista móvil probada.

---

# Cambios ya integrados en esta maqueta

Esta versión de SterakFood ya incluye como base:

- Promos administrables.
- Categoría interna `Salon`.
- Gestor visual del menú.
- Precio rápido desde Dashboard.
- Editor completo de productos.
- Selector de categorías buscable.
- Guardar y cargar otro producto.
- Mozos administrables.
- Mesa rápida con número + Enter.
- Asignación de mozo por mesa.
- Cobro real de mesas al cierre de caja.
- Efectivo / Mercado Pago / Débito en Salón.
- Opiniones privadas con mesa/persona/mozo.
- Pestaña Opiniones en Dashboard.
- Google Reviews configurable.
- Modal de bienvenida opcional.
- Bloque de opiniones compacto.
- Ticketera configurable por variables de entorno.

Esta carpeta debe considerarse la **base maestra**. Para cada cliente nuevo, duplicala y seguí esta guía.
