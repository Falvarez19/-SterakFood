"""Recupera capturas perdidas por cierre inesperado después del commit.

Solo mira operaciones creadas después de la instalación de 6E (no duplica el pasado).
Los cambios de cuentas anteriores se envían cuando vuelven a editarse.
"""
from django.conf import settings
from .models import Desktop6eSettings


def reconcile(max_por_tipo=600):
    if not getattr(settings,'STERAK_DESKTOP_MODE',False):return 0
    from pedidos.models import (Pedido, PedidoParaLlevar, CuentaCorriente,
        MovimientoCuentaCorriente, CorteHistorialVentas)
    from .capture import (capturar_pedido,capturar_para_llevar,
                          capturar_cuenta,capturar_movimiento,capturar_corte)
    cfg,_=Desktop6eSettings.objects.get_or_create(pk=1)
    desde=cfg.created_at
    total=0
    # Usamos created_at de la primera instalación, NO el inicio del programa.
    tareas=(
        (Pedido.objects.filter(fecha_creacion__gte=desde),capturar_pedido),
        (PedidoParaLlevar.objects.filter(pedido__fecha_creacion__gte=desde),capturar_para_llevar),
        (CuentaCorriente.objects.filter(fecha_creacion__gte=desde),capturar_cuenta),
        (MovimientoCuentaCorriente.objects.filter(fecha__gte=desde),capturar_movimiento),
        (CorteHistorialVentas.objects.filter(fecha__gte=desde),capturar_corte),
    )
    for qs,func in tareas:
        for pk in qs.order_by('pk').values_list('pk',flat=True)[:max_por_tipo]:
            func(pk)
            total+=1
    return total
