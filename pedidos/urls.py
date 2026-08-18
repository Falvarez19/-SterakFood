from django.views.generic import TemplateView
from django.contrib import admin
from django.urls import path
from . import views

app_name = 'pedidos'

urlpatterns = [
    # ==========================================
    # 1. RUTAS PÚBLICAS (CLIENTES)
    # ==========================================
    path('admin/', admin.site.urls),
    path('', views.inicio, name='inicio'),
    # urls de pago
    path('webhook-nave/', views.webhook_nave, name='webhook_nave'),
    path('exito-nave/<int:pedido_id>/', views.pago_exitoso_nave, name='pago_exitoso_nave'),
    path('webhook-mp/', views.webhook_mercadopago, name='webhook_mercadopago'),
    
    # ==========================================
    # 2. RUTAS DEL CARRITO DE COMPRAS
    # ==========================================
    path('carrito/agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/sumar/<str:llave>/', views.sumar_carrito, name='sumar_carrito'),
    path('carrito/limpiar/', views.limpiar_carrito, name='limpiar_carrito'),
    path('carrito/ver/', views.ver_carrito, name='ver_carrito'),
    path('carrito/eliminar/<str:llave>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('carrito/restar/<str:llave>/', views.restar_del_carrito, name='restar_del_carrito'),
    
    # ==========================================
    # 3. PROCESAMIENTO DE PEDIDOS (AJAX)
    # ==========================================
    path('procesar/', views.procesar_pedido, name='procesar_pedido'),
    path('exito/<int:pedido_id>/', views.pago_exitoso, name='pago_exitoso'),    
    path('api/pedido/<int:pedido_id>/estado/', views.estado_pedido_api, name='api_estado_pedido'),
    
    # 🔥 ACÁ ESTÁ LA RUTA QUE TE FALTABA PARA EVITAR EL 404 🔥
    path('seguimiento/<int:pedido_id>/', views.seguimiento_pedido, name='seguimiento_pedido'),

    # ==========================================
    # 4. RUTAS DEL DASHBOARD (PANEL DE CONTROL)
    # ==========================================
    path('dashboard/', views.panel_control, name='panel_control'),
    path('dashboard/agregar/', views.agregar_producto, name='agregar_producto'),
    path('dashboard/eliminar/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    path('dashboard/editar-precio/<int:producto_id>/', views.editar_precio, name='editar_precio'),
    path('dashboard/producto/toggle/<int:producto_id>/', views.cambiar_disponibilidad, name='cambiar_disponibilidad'),
    path('dashboard/puesto/toggle/<int:puesto_id>/', views.cambiar_estado_puesto, name='cambiar_estado_puesto'),
    path('dashboard/pedido/eliminar/<int:pedido_id>/', views.eliminar_pedido, name='eliminar_pedido'),
    path('dashboard/item/eliminar/<int:item_id>/', views.eliminar_item_pedido, name='eliminar_item_pedido'),
    path('dashboard/eliminar-todo/', views.eliminar_todo_historial, name='eliminar_todo_historial'),
    path('dashboard/producto/<int:producto_id>/actualizar-puestos/', views.actualizar_producto_puestos, name='actualizar_producto_puestos'),
    path('dashboard/pedido/<int:pedido_id>/estado/<str:nuevo_estado>/', views.cambiar_estado_pedido, name='cambiar_estado_pedido'),
    path('dashboard/login/', views.login_dashboard, name='login_dashboard'),
    path('dashboard/producto/nuevo/', views.agregar_producto, name='agregar_producto'),
    path('dashboard/producto/editar/<int:producto_id>/', views.editar_producto, name='editar_producto'),
    path('cambiar-estado-global/', views.cambiar_estado_global, name='cambiar_estado_global'),
    path('dashboard/backup/', views.descargar_backup_secreto, name='descargar_backup'),
    path('api/resumen-ventas/', views.api_resumen_ventas, name='api_resumen_ventas'),

    # ==========================================
    # 5. API PARA TICKETERA LOCAL (NUEVO)
    # ==========================================
    path('api/pedidos-pendientes/', views.api_pedidos_pendientes, name='api_pedidos_pendientes'),
    path('api/marcar-impreso/<int:pedido_id>/', views.api_marcar_impreso, name='api_marcar_impreso'),
    path('ticket-mesa/<int:pedido_id>/', views.ticket_mesa, name='ticket_mesa'),

    # ==========================================
    # 6. VOLVIENDOLO UNA APP
    # ==========================================
    path('manifest.json', TemplateView.as_view(template_name='manifest.json', content_type='application/json')),
    path('sw.js', TemplateView.as_view(template_name='sw.js', content_type='application/javascript')),

]