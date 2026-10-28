from datetime import time
# SISTEMA SM: modelos de datos del buffet
from django.db import models
# ==========================================
# MODELO: PUNTO DE VENTA (Mostradores físicos)
# ==========================================
class PuntoVenta(models.Model):
    nombre = models.CharField(max_length=50) # Ej: "Parrilla Cancha"
    slug = models.SlugField(max_length=50, unique=True) # ID amigable para la URL
    telefono = models.CharField(max_length=20, help_text="1169544042") # Teléfono para WhatsApp
    abierto = models.BooleanField(default=True) # Interruptor para pausar ventas
    def __str__(self):
        return self.nombre
# ==========================================
# MODELO: CATEGORÍA (Para agrupar en el menú)
# ==========================================
class Categoria(models.Model):
    nombre = models.CharField(max_length=100) # Ej: "Pastas", "Bebidas"
    def __str__(self):
        return self.nombre
# ==========================================
# MODELO: PRODUCTO (Platos y bebidas)
# ==========================================
class Producto(models.Model):
    # Relaciones
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos')
    puntos_venta = models.ManyToManyField(PuntoVenta, related_name='productos')
    # Datos básicos
    nombre = models.CharField(max_length=200)
    codigo_rapido = models.CharField(max_length=20, blank=True, null=True, help_text="Ej: 114 (Gaseosa), 216 (Milanesa)")
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    disponible = models.BooleanField(default=True)
    # Producto destacado en la sección PROMOS del menú.
    # Se activa/desactiva desde el Dashboard.
    en_promocion = models.BooleanField(
        default=False,
        verbose_name="Mostrar en Promos",
    )
    imagen = models.ImageField(
        upload_to='productos_img/',
        null=True,
        blank=True,
    )
    # Opciones de personalización (Se muestran como selects en el Frontend)
    variantes = models.CharField(max_length=255, blank=True, null=True)
    guarniciones = models.CharField(max_length=255, blank=True, null=True)
    puntos_coccion = models.CharField(max_length=255, blank=True, null=True)
    rellenos = models.CharField(max_length=255, blank=True, null=True)
    # Opciones con precios dinámicos (El sistema busca el formato (+XXX))
    salsas = models.CharField(max_length=255, blank=True, null=True, help_text="Ej: Fileto, Bolognesa (+800)")
    adicionales = models.CharField(max_length=255, blank=True, null=True, help_text="Ej: Sin Limón, Con Limón (+500) | Normal, Cargado (+1500)")
    opcion_hielo = models.CharField(max_length=255, blank=True, null=True, help_text="Ej: Con Hielo, Sin Hielo")
    # 🔥 NUEVO CAMPO PARA ORDENAR EL MENÚ 🔥
    orden = models.IntegerField(default=0, help_text="Posición en el menú (1 va primero, 2 después, etc.)")
    # 🔥 ESTO LE DICE A DJANGO CÓMO ORDENARLOS AUTOMÁTICAMENTE 🔥
    class Meta:
        ordering = ['orden', 'nombre']
    def __str__(self):
        return self.nombre
# ==========================================
# MODELO: PEDIDO (El ticket general del cliente)
# ==========================================
class Pedido(models.Model):
    ESTADOS_PEDIDO = [
        ('pendiente', 'Pendiente'),
        ('preparacion', 'En Preparación'),
        ('listo', '¡Listo!'),
        ('cancelado', 'Cancelado'),
    ]
    # Metadatos del pedido
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_PEDIDO, default='pendiente')
    mercado_pago_id = models.CharField(max_length=100, blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # Datos del Cliente
    nombre_cliente = models.CharField(max_length=100, blank=True, null=True)
    telefono_cliente = models.CharField(max_length=20, blank=True, null=True)
    # Logística
    tipo_entrega = models.CharField(max_length=50, default='mostrador')
    numero_mesa = models.CharField(max_length=10, blank=True, null=True)
    # Guarda el mozo responsable cuando la venta proviene del POS de Salón.
    mozo = models.CharField(max_length=100, blank=True, default='')
    tipo_pago = models.CharField(max_length=50, default='mercadopago')
    punto_venta = models.ForeignKey(PuntoVenta, on_delete=models.PROTECT, related_name='pedidos', null=True)
    # Flag para sistema de impresión local (Tickera)
    impreso_caja = models.BooleanField(default=False)
    # v155: sale retained in DB, but excluded from current POS reports after a manual cut.
    archivado_ventas = models.BooleanField(default=False, db_index=True)
    corte_ventas = models.ForeignKey(
        'CorteHistorialVentas', on_delete=models.PROTECT,
        related_name='pedidos_archivados', null=True, blank=True,
    )
    def __str__(self):
        puesto = self.punto_venta.nombre if self.punto_venta else "General"
        return f"Pedido #{self.id} [{puesto}] - {self.get_estado_display()}"
# Pedidos POS para llevar: metadata independiente y clave de idempotencia.
# El Pedido existente sigue siendo la fuente de productos, importes y estados.
class PedidoParaLlevar(models.Model):
    pedido = models.OneToOneField('Pedido', on_delete=models.CASCADE, related_name='para_llevar')
    solicitud_id = models.UUIDField(unique=True, db_index=True)
    observaciones = models.TextField(blank=True, default='')
    fecha_cobro = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Pedido para llevar'
        verbose_name_plural = 'Pedidos para llevar'

    def __str__(self):
        return f'Para llevar #{self.pedido_id}'


# ==========================================
# MODELO: DETALLE PEDIDO (Cada ítem dentro del ticket)
# ==========================================
class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2) # Precio base + extras sumados
    # Registro de lo que seleccionó el cliente para este ítem específico
    variante_elegida = models.CharField(max_length=100, blank=True, null=True)
    guarnicion_elegida = models.CharField(max_length=100, blank=True, null=True)
    punto_coccion_elegido = models.CharField(max_length=100, blank=True, null=True)
    relleno_elegido = models.CharField(max_length=100, blank=True, null=True)
    salsa_elegida = models.CharField(max_length=100, blank=True, null=True)
    adicional_elegido = models.CharField(max_length=100, blank=True, null=True)
    hielo_elegido = models.CharField(max_length=100, blank=True, null=True)
    # Atención alimentaria solicitada para ESTE plato. NO certifica que sea libre de gluten.
    aviso_celiaco = models.BooleanField(default=False)
    def __str__(self):
        nombre = self.producto.nombre if self.producto else "Producto Eliminado"
        return f"{self.cantidad} x {nombre} (Pedido #{self.pedido.id})"
    # ==========================================
# MODELO: CONFIGURACIÓN GLOBAL (Interruptor Maestro)
# ==========================================
class Configuracion(models.Model):
    buffet_habilitado = models.BooleanField(default=True, verbose_name="Aceptar pedidos online")
    descuento_efectivo_activo = models.BooleanField(default=True, verbose_name="Descuento en efectivo")
    descuento_efectivo_porcentaje = models.PositiveSmallIntegerField(default=10, verbose_name="Porcentaje de descuento")
    cierre_automatico_activo = models.BooleanField(default=False, verbose_name="Cierre automático")
    hora_cierre = models.TimeField(default=time(23, 0), verbose_name="Hora de cierre")
    mostrar_promociones = models.BooleanField(default=True, verbose_name="Mostrar promociones")
    mostrar_opiniones = models.BooleanField(default=True, verbose_name="Mostrar opiniones")
    mostrar_google_reviews = models.BooleanField(default=True, verbose_name="Mostrar Google Reviews")
    mostrar_bienvenida = models.BooleanField(default=False, verbose_name="Mostrar bienvenida")
    salon_habilitado = models.BooleanField(default=True, verbose_name="Módulo Salón / Mesas")

    def __str__(self):
        return "Configuración del Buffet"

    class Meta:
        verbose_name_plural = "Configuración"


# ==========================================
# MODELO: MOZOS / PERSONAL DE SALÓN
# ==========================================
class Mozo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


# ==========================================
# MODELO: OPINIONES PRIVADAS DE CLIENTES
# ==========================================
class OpinionCliente(models.Model):
    TIPO_CHOICES = [
        ('atencion', 'Atención'),
        ('comida', 'Comida'),
        ('demora', 'Demora'),
        ('otro', 'Otro'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='atencion')
    mensaje = models.TextField()
    mesa = models.CharField(max_length=20, blank=True)
    nombre = models.CharField(max_length=100, blank=True)
    mozo = models.CharField(max_length=100, blank=True, default='')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    leida = models.BooleanField(default=False)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.fecha_creacion.strftime('%d/%m %H:%M')}"


# SAN MARTIN - CUENTAS CORRIENTES / COMPROBANTES DE DEUDA
# MODELO: CUENTAS CORRIENTES DE CLIENTES
# ==========================================
class CuentaCorriente(models.Model):
    nombre = models.CharField(max_length=120)
    telefono = models.CharField(max_length=30, blank=True, default='')
    nota = models.TextField(blank=True, default='')
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Cuenta corriente'
        verbose_name_plural = 'Cuentas corrientes'

    def __str__(self):
        return self.nombre

    @property
    def saldo_actual(self):
        total = self.movimientos.aggregate(total=models.Sum('monto')).get('total')
        return total or 0


class MovimientoCuentaCorriente(models.Model):
    TIPO_CHOICES = [
        ('consumo', 'Consumo'),
        ('pago', 'Pago'),
        ('favor', 'Dinero a favor'),
        ('ajuste', 'Ajuste manual'),
    ]

    cuenta = models.ForeignKey(
        CuentaCorriente,
        related_name='movimientos',
        on_delete=models.CASCADE,
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='consumo')
    descripcion = models.CharField(max_length=180, blank=True, default='')
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    # Identificador único del cobro POS: evita duplicar deudas ante reintentos.
    operacion_id = models.CharField(max_length=64, blank=True, null=True, unique=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Movimiento de cuenta corriente'
        verbose_name_plural = 'Movimientos de cuentas corrientes'

    def __str__(self):
        return f'{self.cuenta.nombre} - {self.get_tipo_display()} - {self.monto}'


# SterakFood v105 - Comprobantes no fiscales de cuenta corriente y cola de caja
class ComprobanteCuentaCorriente(models.Model):
    cuenta = models.ForeignKey(CuentaCorriente, on_delete=models.CASCADE, related_name='comprobantes')
    movimiento = models.OneToOneField(
        MovimientoCuentaCorriente, related_name='comprobante_pos',
        on_delete=models.CASCADE, blank=True, null=True,
    )
    tipo = models.CharField(max_length=20, default='consumo')  # consumo / estado
    cliente_nombre = models.CharField(max_length=120)
    mesa = models.CharField(max_length=20, blank=True, default='')
    mozo = models.CharField(max_length=100, blank=True, default='')
    items = models.JSONField(default=list)  # Snapshot: no cambia si cambia el producto
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo_anterior = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo_posterior = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Comprobante de cuenta corriente'
        verbose_name_plural = 'Comprobantes de cuenta corriente'


class ImpresionComprobanteCuenta(models.Model):
    comprobante = models.ForeignKey(
        ComprobanteCuentaCorriente, on_delete=models.CASCADE, related_name='impresiones'
    )
    impreso = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_impreso = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['fecha_creacion', 'id']
        verbose_name = 'Impresión pendiente de cuenta'
        verbose_name_plural = 'Impresiones pendientes de cuenta'


# SAN MARTÍN v130: primera etapa de migración fiscal desde DTMaxNet.
# IMPORTANTE: estos modelos NO emiten facturas ni representan comprobantes autorizados.
class ConfiguracionFiscal(models.Model):
    """Datos públicos del emisor para preparar la futura integración con ARCA."""
    CONDICIONES_IVA = [
        ('ri', 'Responsable inscripto'),
        ('monotributo', 'Monotributista'),
        ('exento', 'Exento'),
        ('otro', 'Otra condición'),
    ]
    razon_social = models.CharField(max_length=180, blank=True, default='')
    cuit = models.CharField(max_length=11, blank=True, default='')
    condicion_iva = models.CharField(max_length=20, choices=CONDICIONES_IVA, default='ri')
    punto_venta_referencia = models.PositiveIntegerField(null=True, blank=True,
        help_text='Solo referencia del sistema anterior. No asigna ni habilita un punto de venta en ARCA.')
    domicilio_fiscal = models.CharField(max_length=220, blank=True, default='')
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración fiscal (preparación)'
        verbose_name_plural = 'Configuración fiscal (preparación)'

    def __str__(self):
        return self.razon_social or 'Datos fiscales pendientes de confirmar'


class BorradorFiscal(models.Model):
    """Copia preliminar para auditoría; nunca una factura válida."""
    operacion_id = models.UUIDField(unique=True, editable=False)
    mesa = models.CharField(max_length=10)
    mozo = models.CharField(max_length=100, blank=True, default='')
    items = models.JSONField(default=list)
    total_estimado = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, default='borrador', editable=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Borrador fiscal NO EMITIDO'
        verbose_name_plural = 'Borradores fiscales NO EMITIDOS'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'Mesa {self.mesa} · BORRADOR SIN CAE #{self.pk}'


class RespaldoMesasLocal(models.Model):
    """Copia de emergencia de comandas abiertas de una unica terminal.

    Exclusivo del modo local. No reemplaza un futuro modelo multi-caja.
    """
    version = models.PositiveBigIntegerField(default=0)
    datos = models.JSONField(default=dict)
    modificado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Respaldo de mesas local'


# Replica de lectura de los pedidos QR recibidos en Render.
# NO crear Pedido ni DetallePedido locales: no contabilizar ventas dos veces.
class PedidoQRRemoto(models.Model):
    origen_id = models.PositiveBigIntegerField(unique=True)
    estado = models.CharField(max_length=20, blank=True)
    cliente = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    tipo_pago = models.CharField(max_length=50, blank=True)
    entrega = models.CharField(max_length=50, blank=True)
    mesa = models.CharField(max_length=10, blank=True)
    mostrador = models.CharField(max_length=80, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_remota = models.DateTimeField()
    productos = models.JSONField(default=list)
    ultima_consulta = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_remota', '-origen_id']


class EstadoSyncQR(models.Model):
    ultima_conexion = models.DateTimeField(null=True, blank=True)
    ultimo_error = models.CharField(max_length=250, blank=True)
    ultima_cantidad = models.PositiveIntegerField(default=0)


# v155 - Each manual sales reset is recorded; NO sales or debtor data is deleted.
class CorteHistorialVentas(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    cantidad_pedidos = models.PositiveIntegerField(default=0)
    total_archivado = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    origen = models.CharField(max_length=40, default='panel')

    class Meta:
        ordering = ['-fecha', '-id']
        verbose_name = 'Reinicio de historial de ventas'
        verbose_name_plural = 'Reinicios de historial de ventas'

    def __str__(self):
        return f'Corte #{self.id} · {self.fecha:%d/%m/%Y %H:%M}'


# v157 - Configuración de la impresora del local. No se comparte con clientes.
class ConfiguracionImpresorasPOS(models.Model):
    nombre = models.CharField(max_length=80, default='Terminal principal')
    caja_windows = models.CharField(max_length=120, default='FACTURA_PYTHON')
    ip_cocina = models.GenericIPAddressField(protocol='IPv4', default='192.168.1.100')
    ip_barra = models.GenericIPAddressField(protocol='IPv4', default='192.168.1.101')
    ancho_ticket = models.PositiveSmallIntegerField(default=32)
    token_hash = models.CharField(max_length=64, blank=True, default='')
    actualizado = models.DateTimeField(auto_now=True)
    ultima_conexion = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Configuración impresora POS'
        verbose_name_plural = 'Configuración impresoras POS'


# SAN MARTIN v145: libro de operaciones POS. En modo local es cola pendiente;
# en Render es constancia idempotente de operaciones ya aceptadas.
import uuid as _uuid_pos
class EventoSyncPOS(models.Model):
    id = models.UUIDField(primary_key=True, default=_uuid_pos.uuid4, editable=False)
    tipo = models.CharField(max_length=16)  # venta o producto
    payload = models.JSONField(default=dict)
    creado = models.DateTimeField(auto_now_add=True)
    enviado = models.BooleanField(default=False)
    enviado_en = models.DateTimeField(null=True, blank=True)
    error = models.CharField(max_length=240, blank=True, default='')

    class Meta:
        ordering = ['creado', 'id']
        verbose_name = 'Evento POS para sincronizar'


# Facturas fiscales reales: separado de los borradores y de la caja POS.
class FacturaFiscal(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente de solicitar'),
        ('incierto', 'Verificar en ARCA antes de reintentar'),
        ('autorizada', 'Autorizada con CAE'),
        ('rechazada', 'Rechazada por ARCA'),
    ]
    borrador = models.OneToOneField('BorradorFiscal', on_delete=models.PROTECT, related_name='factura_real')
    estado = models.CharField(max_length=16, choices=ESTADOS, default='pendiente', db_index=True)
    entorno = models.CharField(max_length=20)
    cuit_emisor = models.CharField(max_length=11)
    punto_venta = models.PositiveIntegerField()
    tipo_comprobante = models.PositiveSmallIntegerField(default=6)
    numero = models.PositiveIntegerField(null=True, blank=True)
    fecha_comprobante = models.CharField(max_length=8, blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    neto_21 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    iva_21 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cae = models.CharField(max_length=20, blank=True)
    vencimiento_cae = models.CharField(max_length=8, blank=True)
    url_qr = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)
    impresion_confirmada = models.BooleanField(default=False, db_index=True)
    fecha_impresion = models.DateTimeField(null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-creado']
        constraints = [
            models.UniqueConstraint(fields=['entorno','cuit_emisor','punto_venta','tipo_comprobante','numero'],
                                    name='unica_factura_arca_numero'),
        ]

    def __str__(self):
        return f"{self.entorno}: B-{self.punto_venta:05d}-{(self.numero or 0):08d} {self.estado}"
