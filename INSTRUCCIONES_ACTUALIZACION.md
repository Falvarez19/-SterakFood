# SterakFood — actualización consolidada desde San Martín POS (28/10/2026)

## Alcance

Esta copia parte de `-SterakFood (2).zip`, conserva **SisPedidos** y los logos de SterakFood.
Integra las funciones del salón y panel revisadas en San Martín, además del parche fiscal manual ARCA.
**NO es una versión validada en producción**: requiere pruebas de Django y una base de datos de staging.
No contiene bases de datos, `.env`, certificados, catálogos privados ni Git.

### Funciones incorporadas
- Salón POS moderno: herramientas, mesas, mozos, cobros, división, edición de catálogo y navegación.
- Cuentas corrientes, saldar deuda, control/reinicio seguro de historial y ventas.
- Pedidos QR y actualizaciones del panel (sin duplicaciones previstas por la lógica existente).
- Configuración de ticketera desde el panel y enlace por token.
- ARCA WSAA + WSFEv1, borrador y Factura B, asterisco `*` **manual**, CAE y QR.
- Cola separada de tickets fiscales tras autorización. Cobrar con débito **no factura automáticamente**.

### Limitaciones y advertencias
- ARCA sigue **deshabilitado**: `ARCA_FISCAL_ENABLED=0`. Sin pruebas de homologación ni impresión física.
- El módulo fiscal está integrado en `pedidos` por ahora; antes de comercializar de forma multiempresa, desacoplarlo y aislar los datos/credenciales por tenant. Cada instalación independiente usa los de su propietario.
- La factura soportada inicialmente es **B consumidor final al 21%**; confirmar impuestos y receptor con asesor fiscal antes de producción.
- No activar ARCA producción con DTMaxNet facturando en el mismo PV sin procedimiento anti-colisiones.
- La nube no accede directamente a impresoras USB: el `ticketera.py` del cliente debe seguir activo como **agente de impresión**, no como POS local.
- **PIN del panel:** ahora exige `PANEL_PIN` en variables de entorno; sin ese valor el inicio de sesión queda bloqueado por seguridad.
- Los valores de redes/impresoras deben ajustarse a cada local. No copiar IP ni certificados de San Martín.

### Instalación en copia / staging
1. Respaldar Git y base de datos de SterakFood. **NO extraer encima de producción.**
2. Crear un despliegue de pruebas con PostgreSQL de pruebas, credenciales distintas de San Martín y variables `.env.example`.
3. `pip install -r requirements.txt`
4. `python manage.py check`
5. `python manage.py makemigrations --check --dry-run` (debe indicar sin cambios; si indica diferencia, revisarla sin ejecutar sobre producción).
6. `python manage.py migrate --plan` y luego `python manage.py migrate` SOLO EN STAGING.
7. Verificar `/`, `/menu/`, `/salon/`, `/dashboard/login/`, `/dashboard/`, QR, cobros, cuenta corriente, ventas y configuración de impresoras.
8. Si todo pasa, hacer respaldo y desplegar en la instancia de cada cliente.

### Migraciones
Conservamos íntegra la historia propia de SterakFood `0001…0017`; las migraciones nuevas de SM agregadas son `0018…0025`. Hay divergencia histórica en `0012…0014`, por eso **no** se sobrescribieron las migraciones antiguas. La 0018 apunta a la 0017 que existe en SterakFood.

### Pendientes de comercialización
Autenticación de usuarios por roles (reemplazar PIN único), auditoría, pruebas del flujo fiscal ante caídas y facturas duplicadas, impuestos por línea, validación fiscal por contribuyente, mecanismo de impresión fiable, permisos multiempresa, onboarding por cliente, términos/licencias, monitoreo, backups y actualización segura.

### Protección de datos
No compartir archivos `.p12`, tokens ni `.env` por repositorios públicos. Considerar rotar credenciales anteriores de DTMaxNet.

### Seguridad heredada corregida
- Se eliminó el token Green API, el teléfono fijo para WhatsApp y el PIN fijo heredados del código.
- **Rotar/revocar la clave antigua de Green API**, ya que estuvo guardada en una copia previa del proyecto.
- Configurar `GREEN_API_URL`, `GREEN_API_INSTANCE`, `GREEN_API_TOKEN`, `RESTAURANT_WHATSAPP`, `PANEL_PIN` y `SECRET_KEY` por instalación.
- Sin credenciales de Green API, las notificaciones WhatsApp externas quedan desactivadas.
