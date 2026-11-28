"""6E: cola inmutable local + acuses remotos. No duplica Pedido ni FacturaFiscal."""
import uuid
from django.db import models


class Desktop6eDevice(models.Model):
    # UUID de esta terminal, no del restaurante web; permanece en SQLite.
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Desktop6eSettings(models.Model):
    # Desactivado hasta desplegar servidor y aprobar prueba manual.
    created_at = models.DateTimeField(auto_now_add=True)
    enviar_automaticamente = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)


class Desktop6eOutbox(models.Model):
    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(max_length=32)
    origen = models.CharField(max_length=110)
    payload = models.JSONField()
    digest = models.CharField(max_length=64)
    status = models.CharField(max_length=12, default='pendiente', db_index=True)
    intentos = models.PositiveIntegerField(default=0)
    error = models.CharField(max_length=240, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['tipo', 'origen'], name='sf6e_outbox_origen_unico')]
        ordering = ['created_at', 'event_id']


class Desktop6eInbox(models.Model):
    # Solo se utiliza en Render, en otra base de datos totalmente independiente.
    event_id = models.UUIDField(primary_key=True, editable=False)
    device_id = models.UUIDField()
    installation_id = models.UUIDField()
    tipo = models.CharField(max_length=32)
    origen = models.CharField(max_length=110)
    payload = models.JSONField()
    digest = models.CharField(max_length=64)
    token_label = models.CharField(max_length=80, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['device_id', 'tipo', 'origen'], name='sf6e_inbox_origen_unico')]
        ordering = ['-received_at']
