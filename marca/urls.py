from django.urls import path
from . import views
from .arca_diagnostico_4f import diagnosticar_arca
from .arca_boveda_5b import comprobar_boveda_5b  # STERAKFOOD_5B_RUTAS
from .arca_autogestion_5a import (  # STERAKFOOD_5A_RUTAS
    cargar_certificado_5a, verificar_arca_5a, activar_arca_5a, desactivar_arca_5a,
)

app_name = 'marca'
urlpatterns = [
    path('arca/diagnosticar/', diagnosticar_arca, name='arca_diagnosticar'),
    path('arca/certificado/', cargar_certificado_5a, name='arca_cargar_certificado_5a'),
    path('arca/verificar/', verificar_arca_5a, name='arca_verificar_5a'),
    path('arca/activar/', activar_arca_5a, name='arca_activar_5a'),
    path('arca/desactivar/', desactivar_arca_5a, name='arca_desactivar_5a'),
    path('arca/comprobar-boveda/', comprobar_boveda_5b, name='arca_comprobar_boveda_5b'),
    path('arca/', views.arca_propietario, name='arca_propietario'),
    path('acceso/', views.acceso, name='acceso'),
    path('', views.configurar, name='configurar'),
    path('tema.css', views.tema_css, name='tema_css'),
    path('logo.png', views.logo, name='logo'),
    path('logo-claro.png', views.logo_claro, name='logo_claro'),
    path('manifest.webmanifest', views.manifiesto, name='manifiesto'),
]
