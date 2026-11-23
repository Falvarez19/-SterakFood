from django.urls import path
from . import views
from .arca_diagnostico_4f import diagnosticar_arca

app_name = 'marca'
urlpatterns = [
    path('arca/diagnosticar/', diagnosticar_arca, name='arca_diagnosticar'),
    path('arca/', views.arca_propietario, name='arca_propietario'),
    path('acceso/', views.acceso, name='acceso'),
    path('', views.configurar, name='configurar'),
    path('tema.css', views.tema_css, name='tema_css'),
    path('logo.png', views.logo, name='logo'),
    path('logo-claro.png', views.logo_claro, name='logo_claro'),
    path('manifest.webmanifest', views.manifiesto, name='manifiesto'),
]
