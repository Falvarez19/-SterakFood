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

