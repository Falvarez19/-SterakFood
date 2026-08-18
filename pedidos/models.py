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
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    disponible = models.BooleanField(default=True)
    imagen = models.ImageField(upload_to='productos_img/', null=True, blank=True)
    
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
    tipo_pago = models.CharField(max_length=50, default='mercadopago')
    punto_venta = models.ForeignKey(PuntoVenta, on_delete=models.PROTECT, related_name='pedidos', null=True)
    
    # Flag para sistema de impresión local (Tickera)
    impreso_caja = models.BooleanField(default=False)

    def __str__(self):
        puesto = self.punto_venta.nombre if self.punto_venta else "General"
        return f"Pedido #{self.id} [{puesto}] - {self.get_estado_display()}"

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

    def __str__(self):
        nombre = self.producto.nombre if self.producto else "Producto Eliminado"
        return f"{self.cantidad} x {nombre} (Pedido #{self.pedido.id})"
    
    # ==========================================
# MODELO: CONFIGURACIÓN GLOBAL (Interruptor Maestro)
# ==========================================
class Configuracion(models.Model):
    buffet_habilitado = models.BooleanField(default=True, verbose_name="¿Buffet Habilitado?")

    def __str__(self):
        return "Configuración del Buffet"

    class Meta:
        verbose_name_plural = "Configuración"