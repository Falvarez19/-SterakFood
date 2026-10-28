# SterakFood — casilla CELÍACO en pedidos para llevar

Ahora en POS → Para llevar, junto a los datos del cliente, aparece una **casilla grande "CELÍACO (pedido completo)"**. Marcada, las indicaciones de celiaquía se envían en cada producto del pedido, aunque ya se hubiera añadido al carrito.

También permanece la casilla **"CELÍACO (solo este plato)"** cuando se selecciona un artículo. Ambas opciones son independientes: al desmarcar la general se conservan las advertencias individuales.

Al enviar a cocina, el ticket contiene una alerta de celiaquía destacada y las indicaciones (variantes, guarniciones y puntos de cocción), **sin precios**. El importe sigue visible en el POS para cobrar.

**Importante:** marcar esta advertencia no garantiza que los alimentos sean aptos para celíacos. Cocina debe confirmar ingredientes, utensilios y control de contaminación cruzada antes de preparar o aceptar el pedido.

## Instalación

- Si ya instalaste la última versión *SterakFood_Para_Llevar_Comanda_Celiaco_2026_10_28*, podés aplicar **solo el parche** encima: extraé el ZIP conservando el directorio `SterakFood/` y reemplazá los archivos.
- Si no, utilizá el ZIP completo nuevo.
- Hacé push en el repositorio **SterakFood**, no en el de San Martín. Luego actualizá la página con Ctrl+F5 para renovar el JS.
- Esta modificación **no necesita una migración nueva**. La migración previa `0027_detallepedido_aviso_celiaco` sigue siendo necesaria si todavía no fue aplicada.
- No se modificó `ticketera.py` en este parche; sigue siendo necesaria la versión anterior que imprimía la alerta de celiaquía.

**Verificación:** validación HTML/JS, cálculo de marca general/por plato y compilación del archivo de pruebas. No se pudo ejecutar el conjunto completo de pruebas Django en este entorno por faltar la dependencia Django y no haber acceso al índice de paquetes. El comportamiento real de impresión debe verificarse con la ticketera física.
