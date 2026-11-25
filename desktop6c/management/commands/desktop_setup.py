"""Primera puesta en marcha: usuario propietario y PIN separados por PC."""
import json
import secrets
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Crea dueño y PIN locales si aún no existen. Nunca toca Render.'

    def handle(self, *args, **kwargs):
        if not getattr(settings, 'STERAK_DESKTOP_MODE', False):
            raise RuntimeError('Este comando solo funciona con settings_desktop.')
        config = settings.DATA_DIR / 'config.json'
        if not config.exists():
            pin = str(secrets.randbelow(90000000) + 10000000)
            with config.open('x', encoding='utf-8') as handle:
                json.dump({'panel_pin': pin}, handle)
            try:
                config.chmod(0o600)
            except OSError:
                pass
            self.stdout.write(self.style.WARNING('PIN inicial del POS (guardalo): ' + pin))
        User = get_user_model()
        if not User.objects.filter(is_superuser=True).exists():
            password = secrets.token_urlsafe(18)
            User.objects.create_superuser(username='propietario', email='', password=password)
            self.stdout.write(self.style.WARNING('Usuario de vinculación: propietario'))
            self.stdout.write(self.style.WARNING('Clave inicial de vinculación (guardala): ' + password))
        self.stdout.write('Carpeta de datos locales: ' + str(settings.DATA_DIR))
