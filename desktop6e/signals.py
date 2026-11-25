"""Capture after COMMIT so partially created sales can never enter the outbox."""
from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from pedidos.models import (Pedido, PedidoParaLlevar, CuentaCorriente,
                            MovimientoCuentaCorriente, CorteHistorialVentas)


def _despues(funcion, pk):
    if getattr(settings,'STERAK_DESKTOP_MODE',False):
        transaction.on_commit(lambda: funcion(pk), robust=True)


@receiver(post_save, sender=Pedido, dispatch_uid='sf6e_pedido')
def pedido_guardado(sender,instance,**kwargs):
    from .capture import capturar_pedido
    _despues(capturar_pedido,instance.pk)


@receiver(post_save, sender=PedidoParaLlevar, dispatch_uid='sf6e_para_llevar')
def para_llevar_guardado(sender,instance,**kwargs):
    from .capture import capturar_para_llevar, capturar_pedido
    _despues(capturar_para_llevar,instance.pk)
    _despues(capturar_pedido,instance.pedido_id)


@receiver(post_save, sender=CuentaCorriente, dispatch_uid='sf6e_cuenta')
def cuenta_guardada(sender,instance,**kwargs):
    from .capture import capturar_cuenta
    _despues(capturar_cuenta,instance.pk)


@receiver(post_save, sender=MovimientoCuentaCorriente, dispatch_uid='sf6e_movimiento')
def movimiento_guardado(sender,instance,**kwargs):
    from .capture import capturar_movimiento
    _despues(capturar_movimiento,instance.pk)


@receiver(post_save, sender=CorteHistorialVentas, dispatch_uid='sf6e_corte')
def corte_guardado(sender,instance,**kwargs):
    from .capture import capturar_corte
    _despues(capturar_corte,instance.pk)
