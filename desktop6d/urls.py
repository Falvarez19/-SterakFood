from django.urls import path
from . import views

app_name = 'desktop6d'
urlpatterns = [
    path('', views.panel, name='panel'),
    path('impresoras/', views.configurar_impresoras, name='impresoras'),
    path('impresiones/<int:registro_id>/resolver/', views.resolver_incierta, name='resolver_incierta'),
]
