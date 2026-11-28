"""SterakFood 6F.12A: espejo periódico, nunca ejecuta operaciones comerciales."""
import time
import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections
from desktop6e.mesas_sender_6f12 import enviar_estado


class Command(BaseCommand):
    help = 'Envío read-only de mesas locales a Render cada 15 segundos.'

    def handle(self, *args, **kwargs):
        if not getattr(settings, 'STERAK_DESKTOP_MODE', False):
            raise CommandError('Exclusivo de Desktop')
        self.stdout.write('6F.12A: monitor de mesas iniciado (no envía ventas ni cobros).')
        anterior = ''
        ultimo_error = 0.0
        while True:
            close_old_connections()
            try:
                estado = enviar_estado()
                if estado != anterior and not estado.startswith('Estado de mesas sincronizado'):
                    self.stdout.write('6F.12A: ' + estado)
                anterior = estado
            except (ValueError, requests.RequestException) as exc:
                # Registrar sin exponer token, URL ni contenido de comandas.
                if time.monotonic() - ultimo_error >= 120:
                    self.stderr.write('6F.12A: conexión pendiente (' + exc.__class__.__name__ + ').')
                    ultimo_error = time.monotonic()
            except Exception as exc:
                if time.monotonic() - ultimo_error >= 120:
                    self.stderr.write('6F.12A: error local (' + exc.__class__.__name__ + ').')
                    ultimo_error = time.monotonic()
            finally:
                close_old_connections()
            time.sleep(15)
