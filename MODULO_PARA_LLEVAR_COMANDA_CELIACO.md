# SterakFood — Comanda de cocina sin precios + aviso por celiaquía

## Cambios

- `/salon/` → **Para llevar** sigue consultando los productos y todas las opciones del **menú público** (`Producto`, `variantes`, `guarniciones`, `puntos_coccion`, `adicionales`, etc.).
- El precio del producto y de los extras se conserva para el operador, los cobros, las ventas y el historial; **nunca se incluye en la impresión de la cocina**. Los modificadores del menú como `Napolitana (+2500)` se imprimen simplemente `Napolitana`.
- El **punto de cocción**, salsas, adicionales y las observaciones sí se imprimen como instrucciones.
- En el configurador de **cada plato**, se agregó la casilla **«Cliente celíaco — advertir a cocina»**. Una milanesa normal y otra con aviso de celiaquía se guardan en **renglones separados** para que cocina las distinga.
- En la cabecera de **Para llevar** ahora hay una casilla grande **CELÍACO (pedido completo)**. Al marcarla, la solicitud marca todos los platos como aviso de celiaquía, incluidos los agregados antes de activar la casilla. No se pierde el aviso individual si se desmarca la casilla general. La opción individual permanece disponible al elegir un producto.
- El ticket imprime una **ALERTA CELIAQUÍA** destacada y marca el ítem concreto que necesita atención. Esto es una alerta de seguridad, **no una garantía de que el alimento esté libre de gluten**. Cocina debe verificar ingredientes, utensilios, superficies y contaminación cruzada, y confirmar si puede prepararlo con seguridad.
- **Caja** sigue teniendo montos y precios. No se modifican las funciones fiscales ni se factura al cobrar con débito; `*` sigue siendo el único disparador manual.

## Ejemplo de la comanda de cocina

```
--- COCINA ---
*** PARA LLEVAR ***
PEDIDO #12
*** ALERTA CELIAQUIA ***
REVISAR INGREDIENTES APTOS
EVITAR CONTAMINACION CRUZADA
CONFIRMAR CON COCINA ANTES DE PREPARAR
--------------------------------
!!! CELIACO - REVISAR !!!
1x Milanesa
   -> Napolitana
   -> Guarnicion: Papas
   -> Punto: Bien cocido
   -> Extra: Huevo
```

**Sin total y sin precios.**

## Instalación

1. **Hacé un backup de la versión actual de SterakFood**.
2. Si ya tenés el paquete `SterakFood_Para_Llevar_Menu_Publico_2026_10_28.zip`, aplicá el parche nuevo reemplazando sus archivos. Si no, usá el ZIP completo de esta entrega. **No instales esto en San Martín POS**; es para SterakFood.
3. Hacé el deploy con las migraciones Django. La nueva migración es `pedidos.0027_detallepedido_aviso_celiaco`:

   ```bash
   python manage.py migrate
   ```

4. Actualizá y reiniciá **`ticketera.py` en la PC conectada a cocina**, si esa es la forma de impresión configurada. Sin actualizar el agente antiguo, los modificadores de precio del menú podrían seguir saliendo y las advertencias podrían no aparecer.
5. Probá un pedido controlado de dos milanesas: una común y otra marcada para cliente celíaco. Verificá que la comanda de cocina no muestre importes y diferencie ambos platos.
6. Si cocina no puede garantizar preparación apta para celíacos, informar al cliente: una selección en el POS no certifica que el plato sea libre de gluten.

## Verificación realizada

- Django: `check` y `makemigrations --check --dry-run`: sin errores.
- **16 tests del módulo Para llevar**: correctos (incluye precios, variantes, puntos, flag por ítem, envío a cocina e idempotencia).
- Simulación de ticketera: sin precios y con alerta de celiaquía, variante y punto de cocción.
- **Pendiente:** prueba con la ticketera física y una instalación real de SterakFood. No se hizo push ni se modificó ningún servicio Render.
