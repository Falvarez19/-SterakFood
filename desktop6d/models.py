"""Cola de impresión exclusiva del SQLite local; no va a Render en 6D."""
from django.db import models


class ImpresionLocal6D(models.Model):
    TIPOS = [('pedido', 'Pedido'), ('cuenta', 'Comprobante cuenta corriente')]
    DESTINOS = [('cocina', 'Cocina'), ('barra', 'Barra'), ('caja', 'Caja')]
    ESTADOS = [('pendiente', 'Pendiente'), ('enviando', 'Enviando'),
               ('enviado', 'Enviado a dispositivo'), ('incierto', 'Resultado incierto')]
    tipo = models.CharField(max_length=12, choices=TIPOS)
    referencia_id = models.PositiveIntegerField()
    destino = models.CharField(max_length=10, choices=DESTINOS)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='pendiente')
    intentos = models.PositiveSmallIntegerField(default=0)
    ultimo_error = models.CharField(max_length=400, blank=True, default='')
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['tipo', 'referencia_id', 'destino'], name='desktop6d_impresion_unica')]
        ordering = ['-actualizado']


class AjustesDesktop6D(models.Model):
    # Habilitación explícita; no activamos ticketeras automáticamente al instalar.
    impresion_activa = models.BooleanField(default=False)
    actualizado = models.DateTimeField(auto_now=True)
