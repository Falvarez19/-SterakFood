# SISTEMA SM: configuración del panel de administración de Django
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


from .models import FacturaFiscal

@admin.register(FacturaFiscal)
class FacturaFiscalAdmin(admin.ModelAdmin):
    list_display=('id','estado','entorno','punto_venta','numero','total','cae','impresion_confirmada','creado')
    list_filter=('estado','entorno','punto_venta','impresion_confirmada')
    readonly_fields=[f.name for f in FacturaFiscal._meta.fields]
    def has_add_permission(self,request): return False
    def has_change_permission(self,request,obj=None): return False
    def has_delete_permission(self,request,obj=None): return False
