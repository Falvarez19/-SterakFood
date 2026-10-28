# SterakFood — Pedidos para llevar (POS)

## Novedades

En `/salon/` aparece el botón **🥡 Para llevar**. Abre una ventana dentro del mismo POS.

1. Elegí los productos desde el catálogo y sus cantidades.
2. Ingresá nombre/teléfono y observaciones para cocina (opcionales).
3. Indicá **Pendiente de cobro** o el medio ya cobrado: Efectivo, Débito o Mercado Pago.
4. Presioná **Enviar pedido a cocina**. Se guarda una orden real y se agrega automáticamente a la cola existente `api/pedidos-pendientes/`.
5. La ticketera de cocina imprime `PARA LLEVAR`, número de pedido, cliente, observaciones, productos y estado de pago. Todos los ítems del pedido para llevar (incluidas bebidas) se envían **a cocina**, tal como se solicitó.
6. La lista lateral permite cobrar los pendientes, marcar **Listo** y **Entregado**. No se puede entregar sin registrar cobro y sin confirmación de impresión.

### Seguridad y contabilidad

- Requiere sesión del POS y CSRF para crear/cobrar/marcar pedidos.
- Los importes se calculan **en el servidor** con precios reales, no con los valores enviados por el navegador.
- Cada pedido nuevo tiene `solicitud_id` UUID único; reintentar no debe duplicar ventas ni comandas.
- Un pedido **Pendiente de cobro** no se computa como venta cobrada ni genera factura fiscal.
- No afecta el flujo manual `*` de ARCA. Ni Débito ni ningún otro medio emite factura por sí mismo.
- Las ventas para llevar aparecen separadas como `Para llevar` en el cierre del POS.
- La comanda no ocupa mesas ni modifica los saldos del salón.

### Instalación

1. Hacé una copia del proyecto de SterakFood. Reemplazá los archivos del proyecto con los de este ZIP o, si partís exactamente de `SterakFood_Actualizado_SM_2026_10_28.zip`, aplicá el ZIP de parche.
2. Commit/push al repositorio de SterakFood **(no** al repositorio de San Martín POS).
3. El despliegue debe ejecutar `python manage.py migrate` (hay migración nueva `pedidos.0026_pedidoparallevar`).
4. Reiniciá el servicio web y entrá a `/salon/`; verificá el botón `🥡 Para llevar`.
5. Para la impresión, mantené activo el agente de impresión `ticketera.py` que **ya** utilizabas. Debe estar conectado a la URL de SterakFood y a `IP_COCINA` del comercio. El programa viejo DTMaxNet no participa.
6. Creá un pedido de bajo importe de prueba y controlá que aparece `PARA LLEVAR` en la ticketera de cocina, no en la de caja o barra.

**Limitaciones:** se comprobó la lógica Django mediante pruebas automáticas, pero NO la impresión en una ticketera física ni el despliegue en Render. Render no puede imprimir directamente en una USB de tu PC sin un agente o servicio de impresión accesible. Si la impresión física se completa pero la confirmación al servidor se pierde por problemas de red, se podría volver a imprimir la comanda. Revisá el ticket antes de reenviar.

### Comprobaciones de desarrollo

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test pedidos.tests_takeout
```

### Archivos principales

- `pedidos/para_llevar.py`: endpoints, validación, cobro, estados e idempotencia.
- `pedidos/models.py` y `pedidos/migrations/0026_pedidoparallevar.py`: metadatos y notas.
- `pedidos/views.py`: cola de impresión y reportes.
- `pedidos/templates/pedidos/salon.html`: botón y ventana POS.
- `pedidos/static/script/para_llevar_pos.js`: catálogo, carrito, carga y seguimiento.
- `pedidos/static/css/estilos.css`: estilos responsive.
- `ticketera.py`: formato de cocina y manejo de errores.
- `pedidos/tests_takeout.py`: pruebas.

**No incluye certificados, claves fiscales ni bases de datos privadas de San Martín.**
