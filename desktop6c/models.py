"""6C: el catálogo remoto nunca comparte la base de ventas local."""
import uuid
from django.db import models


class WebInstallation(models.Model):
    """ID estable de una instalación web; evita vincular una PC a otro cliente."""
    instance_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)


class DesktopAccessToken(models.Model):
    """Solo almacena el SHA-256 del token, nunca el token original."""
    label = models.CharField(max_length=80)
    token_hash = models.CharField(max_length=64, unique=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)


class DesktopLink(models.Model):
    """En la base SQLite local: credenciales cifradas con la clave de esta PC."""
    server_url = models.URLField(max_length=300)
    web_instance_id = models.UUIDField()
    token_ciphertext = models.TextField()
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=500, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)


class RemoteObjectMap(models.Model):
    """Mapea PK web a PK local sin pisar registros operativos existentes."""
    kind = models.CharField(max_length=16, choices=[('producto', 'Producto'), ('categoria', 'Categoría'), ('puesto', 'Punto de venta')])
    remote_id = models.PositiveIntegerField()
    local_id = models.PositiveIntegerField()
    photo_source = models.CharField(max_length=500, blank=True, default='')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['kind', 'remote_id'], name='desktop6c_remote_unique')]


class DesktopSyncEvent(models.Model):
    """Auditoría técnica local; no contiene tokens ni datos fiscales."""
    created_at = models.DateTimeField(auto_now_add=True)
    ok = models.BooleanField()
    summary = models.CharField(max_length=350)
    products_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
