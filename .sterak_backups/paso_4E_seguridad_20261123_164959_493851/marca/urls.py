from django.urls import path
from . import views

app_name = 'marca'
urlpatterns = [
    path('acceso/', views.acceso, name='acceso'),
    path('', views.configurar, name='configurar'),
    path('tema.css', views.tema_css, name='tema_css'),
    path('logo.png', views.logo, name='logo'),
    path('logo-claro.png', views.logo_claro, name='logo_claro'),
    path('manifest.webmanifest', views.manifiesto, name='manifiesto'),
]
