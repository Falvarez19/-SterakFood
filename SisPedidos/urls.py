"""
URL configuration for PedidosSM project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.urls import re_path
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    # Tu app de pedidos
    path('mi-negocio/', include('marca.urls')),
    path('', include('pedidos.urls')), 
]

#  Fuerza a Django a mostrar fotos aunque estemos en un servidor de Producción
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]

# STERAKFOOD_DESKTOP_6C_URLS
urlpatterns.append(path('desktop/', include('desktop6c.urls')))

# STERAKFOOD_6F12A_MESAS_ROUTES
from desktop6e import mesas_6f12 as _sf12_mesas
urlpatterns += [
    path('desktop/api/v1/mesas-6f12/', _sf12_mesas.recibir_mesas, name='sf12_recibir'),
    path('salon/api/mesas-desktop-6f12/', _sf12_mesas.estado_mesas_web, name='sf12_estado_web'),
]

