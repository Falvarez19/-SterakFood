# SterakFood — Sistema POS gastronómico web

Base comercializable para restaurantes, cafeterías y buffets. Django en servidor (Render/PostgreSQL) y navegador para mesas, catálogo, pedidos QR, cobros, cuentas corrientes y ventas. **No hay POS local**. Las ticketeras de Windows pueden requerir el agente dedicado `ticketera.py` para imprimir sin diálogo.

## Funciones (código actualizado desde San Martín)
- Salón POS: mesas, mozos, división, cobros manuales, cuentas corrientes, Ventas, edición rápida e impresión.
- Menú web, pedidos QR, preferencias del local, panel de administración.
- ARCA WSAA + WSFEv1 en módulo experimental: `*` manual, autorización de Factura B y cola de impresión fiscal.
- Marca y servicios configurables por instalación (`RESTAURANT_NAME`, `PANEL_PIN`, credenciales de WhatsApp y ARCA).

## Instalación
Leer primero **INSTRUCCIONES_ACTUALIZACION.md**. Crear `.env` local fuera de Git con valores de `.env.example`.
El código trae migraciones de `0001` a `0025`, pero **no debe desplegarse en producción sin probar en staging**.

## Seguridad
Las credenciales de terceros que existían en copias anteriores ya no están incluidas. Es necesario **rotar las claves Green API antiguas**. No incluir ningún `.p12` de ARCA ni bases privadas en Git.

## Estado fiscal
La emisión real está **deshabilitada** por defecto. Las pruebas incluidas son simuladas, no se verificó homologación/producción con ARCA ni la impresión física. DTMaxNet puede continuar como respaldo, evitando uso simultáneo del mismo punto de venta fiscal.
