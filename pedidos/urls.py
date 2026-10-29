# SISTEMA SM: rutas de la aplicación Pedidos
from django.views.generic import TemplateView
from django.contrib import admin
from django.urls import path
from . import views, impresoras_views, fiscal_views, para_llevar
app_name = 'pedidos'
urlpatterns = [
    path('salon/fiscal/emitir-manual/', fiscal_views.emitir_manual, name='fiscal_emitir_manual'),
    path('salon/fiscal/consultar/<int:factura_id>/', fiscal_views.consultar_incierta, name='fiscal_consultar_incierta'),
    path('api/tickets-fiscales-pendientes/', fiscal_views.tickets_fiscales_pendientes, name='tickets_fiscales_pendientes'),
    path('api/tickets-fiscales-confirmar/<int:factura_id>/', fiscal_views.confirmar_impresion, name='tickets_fiscales_confirmar'),
    # Panel de impresoras: guarda destinos, no imprime desde Render.
    path('dashboard/impresoras/configuracion/', impresoras_views.impresoras_obtener, name='impresoras_obtener'),
    path('dashboard/impresoras/guardar/', impresoras_views.impresoras_guardar, name='impresoras_guardar'),
    path('dashboard/impresoras/vincular/', impresoras_views.impresoras_vincular, name='impresoras_vincular'),
    path('api/ticketera/configuracion/', impresoras_views.ticketera_configuracion_api, name='ticketera_configuracion_api'),
    path('salon/api/resumen-ventas/', views.salon_resumen_ventas_api, name='salon_resumen_ventas_api'),
    path('salon/api/reiniciar-historial-ventas/', views.reiniciar_historial_ventas, name='reiniciar_historial_ventas'),
    path('salon/api/respaldo-local/', views.respaldo_mesas_local_api, name='respaldo_mesas_local_api'),
    path('salon/estado-ticket/', views.estado_ticket_salon, name='estado_ticket_salon'),
    path('salon/fiscal/', views.fiscal_preparacion, name='fiscal_preparacion'),
    path('salon/fiscal/borrador/', views.fiscal_guardar_borrador, name='fiscal_guardar_borrador'),
    path('salon/fiscal/probar-conexion/', views.fiscal_probar_conexion_arca, name='fiscal_probar_conexion_arca'),
    path('dashboard/cuentas/<int:cuenta_id>/saldar/', views.saldar_cuenta_corriente, name='saldar_cuenta_corriente'),

    # ==========================================
    # 1. RUTAS PÚBLICAS (CLIENTES)
    # ==========================================
    path('admin/', admin.site.urls),
    path('', views.bienvenida, name='bienvenida'),
    path('menu/', views.inicio, name='inicio'),
    path('opinion/enviar/', views.enviar_opinion, name='enviar_opinion'),
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
    path('dashboard/configuracion/actualizar/', views.actualizar_configuracion, name='actualizar_configuracion'),
    path('dashboard/popup-bienvenida/subir/', views.subir_popup_bienvenida, name='subir_popup_bienvenida'),
    path('dashboard/popup-bienvenida/eliminar/', views.eliminar_popup_bienvenida, name='eliminar_popup_bienvenida'),
    path('dashboard/opinion/<int:opinion_id>/leida/', views.marcar_opinion_leida, name='marcar_opinion_leida'),
    path('dashboard/opinion/<int:opinion_id>/eliminar/', views.eliminar_opinion, name='eliminar_opinion'),
    path('dashboard/mozo/agregar/', views.agregar_mozo, name='agregar_mozo'),
    path('dashboard/mozo/<int:mozo_id>/eliminar/', views.eliminar_mozo, name='eliminar_mozo'),
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
    path('api/resumen-ventas/', views.api_resumen_ventas, name='api_resumen_ventas'),
    path('salon/', views.salon, name='salon'),
    path('salon/para-llevar/', para_llevar.pedidos_para_llevar, name='pedidos_para_llevar'),
    path('salon/para-llevar/<int:pedido_id>/cobrar/', para_llevar.cobrar_para_llevar, name='cobrar_para_llevar'),
    path('salon/para-llevar/<int:pedido_id>/estado/', para_llevar.estado_para_llevar, name='estado_para_llevar'),
    path('salon/importar-codigos/', views.importar_codigos_salon, name='importar_codigos_salon'),
    path('salon/catalogo/', views.catalogo_salon_api, name='catalogo_salon_api'),
    path('salon/catalogo/<int:producto_id>/editar/', views.editar_producto_salon, name='editar_producto_salon'),
    path('salon/imprimir-ticket/', views.imprimir_ticket_salon, name='imprimir_ticket_salon'),
    path('salon/cobrar-mesa/', views.cobrar_mesa_salon, name='cobrar_mesa_salon'),
    path('salon/estado-cobro/', views.estado_cobro_salon, name='estado_cobro_salon'),
    # 🔥 NUEVA RUTA PARA DESCARGAR EL BACKUP 🔥
    path('dashboard/backup/', views.descargar_backup_secreto, name='descargar_backup'),
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

    # SAN MARTIN - CUENTAS CORRIENTES Y COMPROBANTES
    path('dashboard/cuentas/crear/', views.crear_cuenta_corriente, name='crear_cuenta_corriente'),
    path('dashboard/cuentas/<int:cuenta_id>/movimiento/', views.agregar_movimiento_cuenta, name='agregar_movimiento_cuenta'),
    path('dashboard/cuentas/<int:cuenta_id>/eliminar/', views.eliminar_cuenta_corriente, name='eliminar_cuenta_corriente'),
    path('dashboard/cuentas/movimiento/<int:movimiento_id>/eliminar/', views.eliminar_movimiento_cuenta, name='eliminar_movimiento_cuenta'),
    path('dashboard/cuentas/comprobante/<int:comprobante_id>/imprimir/', views.imprimir_comprobante_cuenta, name='imprimir_comprobante_cuenta'),
    path('dashboard/cuentas/<int:cuenta_id>/imprimir-estado/', views.imprimir_estado_cuenta, name='imprimir_estado_cuenta'),
    path('salon/api/pedidos-web/', views.salon_pedidos_web_api, name='salon_pedidos_web_api'),
    path('api/tickets-cuenta-pendientes/', views.api_tickets_cuenta_pendientes, name='api_tickets_cuenta_pendientes'),
    path('api/marcar-ticket-cuenta-impreso/<int:trabajo_id>/', views.api_ticket_cuenta_impreso, name='api_ticket_cuenta_impreso'),
]
