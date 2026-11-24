from django.db import models


class MarcaNegocio(models.Model):
    """Identidad de UNA instalación / una base de datos (no multi-tenant)."""
    nombre = models.CharField(max_length=90, default='SterakFood')
    nombre_corto = models.CharField(max_length=45, default='SterakFood')
    subtitulo = models.CharField(max_length=160, blank=True, default='')
    color_principal = models.CharField(max_length=7, default='#FF6600')
    color_secundario = models.CharField(max_length=7, default='#FF6600')
    color_acento = models.CharField(max_length=7, default='#FF8533')
    colores_personalizados = models.BooleanField(default=False)
    # Guardar pocos KB directamente en PostgreSQL/SQLite evita perder el logo
    # con el filesystem efímero de Render y en actualizaciones del instalador.
    logo_png = models.BinaryField(null=True, blank=True, editable=False)
    logo_claro_png = models.BinaryField(null=True, blank=True, editable=False)

    # STERAKFOOD_6A_PERSONALIZACION_VISUAL — solo menú público y Mi negocio.
    menu_fuente = models.CharField(max_length=20, default='original')
    menu_titulo_px = models.PositiveSmallIntegerField(default=32)
    menu_producto_px = models.PositiveSmallIntegerField(default=17)
    menu_descripcion_px = models.PositiveSmallIntegerField(default=14)
    menu_precio_px = models.PositiveSmallIntegerField(default=18)
    menu_color_fondo = models.CharField(max_length=7, default='#121212')
    menu_color_boton = models.CharField(max_length=7, default='#FF6600')
    menu_fondo_archivo = models.BinaryField(null=True, blank=True, editable=False)
    menu_portada_archivo = models.BinaryField(null=True, blank=True, editable=False)
    menu_portada_mime = models.CharField(max_length=32, blank=True, default='')
    menu_mostrar_portada = models.BooleanField(default=True)
    menu_oscurecer = models.PositiveSmallIntegerField(default=40)
    menu_tarjetas_iguales = models.BooleanField(default=True)
    menu_sombra_tarjetas = models.BooleanField(default=True)
    menu_borde_px = models.PositiveSmallIntegerField(default=14)
    menu_boton_estilo = models.CharField(max_length=12, default='normal')

    actualizado = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Personalización del negocio'
        verbose_name_plural = 'Personalización del negocio'

    def __str__(self):
        return self.nombre

# STERAKFOOD_5A_MODELO_ARCA_AUTOGESTION
class ArcaCredencial(models.Model):
    """Una instalación SterakFood = un contribuyente. Cada entorno tiene su P12."""
    id = models.BigAutoField(primary_key=True)
    entorno = models.CharField(max_length=15, unique=True, choices=[
        ('homologacion', 'Homologación'), ('produccion', 'Producción'),
    ])
    cuit = models.CharField(max_length=11)
    punto_venta = models.PositiveIntegerField()
    secreto_cifrado = models.BinaryField(editable=False)
    nombre_archivo = models.CharField(max_length=100, default='certificado.p12')
    huella_sha256 = models.CharField(max_length=64)
    vencimiento = models.DateTimeField()
    ingresos_brutos = models.CharField(max_length=60, blank=True, default='')
    inicio_actividades = models.DateField(null=True, blank=True)
    verificada = models.BooleanField(default=False)
    activa = models.BooleanField(default=False)
    ultimo_chequeo = models.DateTimeField(null=True, blank=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Credencial ARCA cifrada (por entorno)'
        verbose_name_plural = 'Credenciales ARCA cifradas (por entorno)'

    def __str__(self):
        return f'ARCA {self.entorno} - {self.cuit[:2]}*******{self.cuit[-2:]}'


# STERAKFOOD_5H_MODELO_ENSAYO_C
import uuid

class ArcaEnsayoFacturaC(models.Model):
    """Pruebas de homologación aisladas del POS y de FacturaFiscal."""
    operacion_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    entorno = models.CharField(max_length=15, default='homologacion', editable=False)
    cuit_emisor = models.CharField(max_length=11)
    punto_venta = models.PositiveIntegerField()
    numero = models.PositiveIntegerField()
    total = models.DecimalField(max_digits=9, decimal_places=2)
    fecha_comprobante = models.CharField(max_length=8)
    estado = models.CharField(max_length=15, choices=[
        ('incierto', 'Verificar en ARCA antes de reintentar'),
        ('autorizada', 'CAE homologación recibido'),
        ('rechazada', 'Rechazada: requiere revisión'),
    ], default='incierto')
    cae = models.CharField(max_length=20, blank=True, default='')
    vence_cae = models.CharField(max_length=8, blank=True, default='')
    url_qr = models.TextField(blank=True, default='')
    detalle_publico = models.CharField(max_length=240, blank=True, default='')
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ensayo de Factura C (SIN valor fiscal)'
        verbose_name_plural = 'Ensayos de Factura C (SIN valor fiscal)'
        constraints = [
            models.UniqueConstraint(fields=['entorno', 'cuit_emisor', 'punto_venta', 'numero'],
                                    name='sterak_5h_numero_c_unico'),
        ]

