# SterakFood — Para llevar usando el menú público

## Cómo funciona

Dentro de `/salon/` abrí **🥡 Para llevar**. La lista usa **los mismos productos disponibles del menú público**, con su nombre, categoría, foto, precio y las opciones ya cargadas desde el panel de Productos. No crea un catálogo independiente.

- Seleccioná, por ejemplo, **Milanesa**.
- Si el producto tiene variantes, elegí **Común** o **Napolitana**, luego guarnición, cocción, relleno, salsa, hielo y adicionales, según lo que ese producto tenga configurado.
- Los campos con opciones de elección única deben seleccionarse; los adicionales permiten varias opciones o ninguna.
- Las opciones con `( +importe )` sin espacios, por ejemplo `Napolitana (+2500)`, actualizan el total en pantalla **y se vuelven a calcular desde los precios del servidor**.
- Dos versiones diferentes del mismo plato aparecen como dos líneas en el pedido y llegan por separado a cocina.
- Podés agregar nombre/telefono, observaciones y registrar el cobro o dejarlo pendiente.
- Enviar pedido guarda la comanda y la deja en la cola de cocina. La impresión térmica es realizada por el agente de impresoras `ticketera.py` configurado para ese comercio.

## Fuente de datos

Se usa `Producto` / `Categoria` / `PuntoVenta` del menú público. No se muestran los productos de la categoría exclusiva `Salon`. Si hay puntos de venta cargados, se incluyen solamente productos publicados en uno de los puntos abiertos.

Campos reusados del producto (sin duplicación): `variantes`, `guarniciones`, `puntos_coccion`, `rellenos`, `salsas`, `adicionales`, `opcion_hielo`. Se guardan en los campos correspondientes de `DetallePedido` para mantener la elección que tenía el producto al hacer la venta.

## Archivos modificados

- `pedidos/para_llevar.py`: consulta del catálogo público, validación rigurosa de opciones y precios por línea.
- `pedidos/static/script/para_llevar_pos.js`: selector de variantes, adicionales y carrito por combinación.
- `pedidos/templates/pedidos/salon.html`: panel para personalizar el plato.
- `pedidos/static/css/estilos.css`: estilos del selector responsive.
- `pedidos/views.py`: API de impresión agrega campos estructurados `plato` y `opciones`.
- `ticketera.py`: imprime las opciones sin mostrar los suplementos monetarios en cocina y conserva compatibilidad con los tickets anteriores.
- `pedidos/tests_takeout.py`: pruebas de variantes, importes, opciones fraudulentas y cola de cocina.

## Aplicación del parche

1. **Hacé una copia** del proyecto SterakFood actual.
2. Aplicá el ZIP de parche sobre **la versión anterior SterakFood_POS_Para_Llevar_2026_10_28**, reemplazando los archivos incluidos. Si no tenés esa versión, usá el ZIP completo de esta entrega.
3. Reiniciá/desplegá tu SterakFood (no San Martín POS). No hay migraciones nuevas en esta corrección.
4. Ingresá al panel de productos, comprobá que una milanesa tenga en `Variantes` algo como `Común, Napolitana (+2500)` y la guarnición deseada.
5. Entrá a `/salon/` → **Para llevar** → elegí milanesa, seleccioná variante y guarnición, agregá dos configuraciones distintas y enviá una **prueba controlada**.
6. Verificá que la comanda que llega a cocina muestre opciones y puntos de cocción, **sin precios ni total**. Si usás `ticketera.py` en Windows, actualizá ese archivo en el agente y reinicialo.

## Límites y seguridad

- La facturación fiscal ARCA sigue **desactivada por defecto**. Solo el comando manual `*` puede iniciar ese proceso; un cobro por débito no lo hace.
- La API recalcula importes y rechaza productos no publicados, variantes inexistentes y selecciones obligatorias vacías. No confía en el precio enviado por el navegador.
- Las colas de impresión siguen requiriendo el agente que alcanza la ticketera física; no se ha probado aquí con impresora real.
- No se incorporaron certificados fiscales, bases privadas ni claves de San Martín.

**Nota de actualización (28/10):** Ver también `MODULO_PARA_LLEVAR_COMANDA_CELIACO.md`: el nuevo módulo agrega marca de celiaquía por plato y elimina precios de la comanda de cocina.
