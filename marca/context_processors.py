"""Identidad por instalación; los valores predeterminados conservan la estética original."""
from django.db.utils import OperationalError, ProgrammingError
from .models import MarcaNegocio

DEFAULTS = {
    'nombre': 'SterakFood',
    'nombre_corto': 'SterakFood',
    'subtitulo': '',
    'color_principal': '#FF6600',
    'color_secundario': '#FF6600',
    'color_acento': '#FF8533',
    'colores_personalizados': False,
}


def datos_marca():
    try:
        row = MarcaNegocio.objects.filter(pk=1).values(*DEFAULTS.keys()).first()
    except (OperationalError, ProgrammingError):
        row = None  # Antes de migrate, la web conserva su tema actual.
    return {**DEFAULTS, **(row or {})}


def marca_context(request):
    marca = datos_marca()
    # Sobrescribe el nombre genérico del contexto anterior sin modificar la vista.
    return {'marca': marca, 'restaurant_name': marca['nombre']}
