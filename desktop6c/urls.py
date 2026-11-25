from django.urls import path
from . import views, api

app_name = 'desktop6c'
urlpatterns = [
    path('', views.home, name='home'),
    path('web/claves/', views.web_keys, name='web_keys'),
    path('vincular/', views.pair, name='pair'),
    path('sincronizar/', views.sync_now, name='sync_now'),
    path('api/v1/catalogo/', api.catalog, name='catalog'),
    path('api/v1/archivo/<str:kind>/<int:remote_id>/', api.asset, name='image'),
    path('api/v1/archivo/<str:kind>/', api.asset, name='asset'),
]

# STERAKFOOD_DESKTOP_6D_ROUTES
from django.conf import settings
from django.urls import include
if getattr(settings, 'STERAK_DESKTOP_MODE', False):
    urlpatterns += [path('operaciones/', include('desktop6d.urls'))]

# STERAKFOOD_6E_ROUTES
from desktop6e import api as _sf6e_api, views as _sf6e_views
urlpatterns += [
    path('api/v1/operaciones/', _sf6e_api.operaciones, name='api6e_operaciones'),
    path('sync-6e/', _sf6e_views.estado, name='sync6e_status'),
    path('sync-6e/accion/', _sf6e_views.accion, name='sync6e_action'),
    path('web/operaciones-6e/', _sf6e_views.recibidos, name='sync6e_inbox'),
]
