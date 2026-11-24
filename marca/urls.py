from django.urls import path
from . import views
from .arca_diagnostico_4f import diagnosticar_arca
from .arca_simulador_c_5d import simular_factura_c_5d  # STERAKFOOD_5D_RUTAS
from .arca_boveda_5b import comprobar_boveda_5b  # STERAKFOOD_5B_RUTAS
from .arca_autogestion_5a import (  # STERAKFOOD_5A_RUTAS
    cargar_certificado_5a, verificar_arca_5a, activar_arca_5a, desactivar_arca_5a,
)

# STERAKFOOD_6A_PERSONALIZACION_VISUAL
from .visual_6a import menu_fondo, menu_portada, menu_tema_css

from .arca_preflight_c_5g import preflight_factura_c_5g  # STERAKFOOD_5G_PREFLIGHT_C

from .arca_ensayo_c_5h import emitir_ensayo_c_5h, recuperar_ensayo_c_5h, resultado_ensayo_c_5h  # STERAKFOOD_5H_EMISION_HOMOLOGACION

app_name = 'marca'
urlpatterns = [
    path('menu-fondo-6a.webp', menu_fondo, name='menu_fondo_6a'),
    path('menu-portada-6a', menu_portada, name='menu_portada_6a'),
    path('menu-visual-6a.css', menu_tema_css, name='menu_tema_css_6a'),
    path('arca/diagnosticar/', diagnosticar_arca, name='arca_diagnosticar'),
    path('arca/simular-factura-c/', simular_factura_c_5d, name='arca_simular_c_5d'),
    path('arca/preflight-c-homologacion/', preflight_factura_c_5g, name='arca_preflight_c_5g'),
    path('arca/ensayo-c/emitir/', emitir_ensayo_c_5h, name='arca_emitir_ensayo_c_5h'),
    path('arca/ensayo-c/recuperar/', recuperar_ensayo_c_5h, name='arca_recuperar_ensayo_c_5h'),
    path('arca/ensayo-c/resultado/', resultado_ensayo_c_5h, name='arca_resultado_5h'),
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
