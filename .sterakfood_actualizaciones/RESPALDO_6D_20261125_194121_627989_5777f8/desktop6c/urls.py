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
