from django.contrib import admin
from .models import (
    Categoria,
    Producto,
    PuntoVenta,
    Pedido,
    DetallePedido,
    Mozo,
    OpinionCliente,
    Configuracion,
)

class CategoriaAdmin(admin.ModelAdmin):
    pass

admin.site.register(Categoria, CategoriaAdmin)
admin.site.register(Producto)
admin.site.register(PuntoVenta)
admin.site.register(Pedido)
admin.site.register(DetallePedido)
admin.site.register(Mozo)
admin.site.register(OpinionCliente)
admin.site.register(Configuracion)
