"""Proceso local persistente de impresión. No contacta Render ni ARCA."""
import time
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from desktop6d.printing import iteracion


class Command(BaseCommand):
    help = 'Imprime cola local cuando propietario la habilita en 6D.'

    def handle(self, *args, **kwargs):
        if not getattr(settings,'STERAK_DESKTOP_MODE',False):
            raise CommandError('Solo permitido en Desktop local.')
        self.stdout.write('Cola de impresoras 6D local iniciada. Sin imprimir facturas fiscales.')
        while True:
            try:
                iteracion()
            except Exception as exc:
                self.stderr.write('Error de impresoras: '+str(exc)[:240])
            time.sleep(7)
