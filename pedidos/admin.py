from django.contrib import admin
from .models import Categoria, Producto, PuntoVenta, Pedido, DetallePedido

# Registro de la forma más primitiva posible
class CategoriaAdmin(admin.ModelAdmin):
    # No ponemos nada aquí. Si no ponemos nada, 
    # no usa plantillas personalizadas y evita el error.
    pass

admin.site.register(Categoria, CategoriaAdmin)
admin.site.register(Producto)
admin.site.register(PuntoVenta)
admin.site.register(Pedido)
admin.site.register(DetallePedido)