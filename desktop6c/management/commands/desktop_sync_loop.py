import time
from django.core.management.base import BaseCommand
from desktop6c.sync import run_sync


class Command(BaseCommand):
    help = 'Sincroniza cada dos minutos desde web, sin tocar ventas ni caja.'
    def handle(self, *args, **options):
        while True:
            try:
                run_sync()
            except Exception as exc:
                self.stderr.write('Fallo de sincronización: ' + str(exc)[:160])
            time.sleep(120)
