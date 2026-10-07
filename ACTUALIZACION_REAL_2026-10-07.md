# SterakFood — actualización aplicada al archivo real

Esta carpeta fue generada a partir del archivo `-SterakFood(1).zip` enviado el 07/10/2026.

Se conservaron la base SQLite y los archivos `media` del archivo real. No se incluyeron `.env`, `.git`, `venv` ni `__pycache__` en el ZIP final.

## Funciones incorporadas

- Promociones administrables desde Dashboard (`Producto.en_promocion`).
- Categoría interna `Salon` para productos del POS, excluida del menú público.
- Gestor de menú del Dashboard con buscador, filtros, edición completa y precio rápido.
- Carga consecutiva de productos sin volver al panel.
- Gestión de mozos y asignación de mozo a mesa.
- Opiniones privadas con mesa, nombre, mozo y comentario; lectura/eliminación desde Dashboard.
- Enlace opcional a Google Reviews.
- POS de Salón con apertura rápida por número de mesa y teclado.
- Cobros reales de Salón registrados en `Pedido` y contemplados en el cierre de caja.
- Medios de cobro de Salón: efectivo, Mercado Pago y débito.
- Impresión de cuenta de Salón separada del registro de venta, evitando duplicados.
- Sección de opiniones compacta.
- Modal de bienvenida preparado y desactivado por defecto para que cada restaurante use su propia imagen.
- Ticketera reutilizable mediante variables de entorno, sin dominio/nombre del Buffet San Martín clavado en el código.
- Configuración reutilizable para SQLite local o `DATABASE_URL` en producción.

## Importante después de reemplazar los archivos

Ejecutar:

```powershell
python manage.py migrate
python manage.py check
python manage.py runserver
```

Para crear otro restaurante, seguir `GUIA_NUEVO_RESTAURANTE.md`.
