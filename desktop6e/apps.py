"""Registro separado de operaciones POS 6E, sin alterar el libro fiscal."""
from django.apps import AppConfig


class Desktop6eConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'desktop6e'
    verbose_name = 'SterakFood 6E / Sincronización segura'

    def ready(self):
        # Los manejadores verifican STERAK_DESKTOP_MODE antes de capturar.
        from . import signals  # noqa: F401
