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
