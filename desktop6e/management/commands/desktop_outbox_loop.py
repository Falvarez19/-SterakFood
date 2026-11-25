"""Envío lento: controlado por el propietario local. SQLite sobrevive reinicios."""
import time
from django.conf import settings
from django.core.management.base import BaseCommand
from desktop6e.sender import enviar_pendientes, ReceptorNoListo
from desktop6e.reconcile import reconcile


class Command(BaseCommand):
    help = '6E: enviar cola offline solamente si fue autorizada.'

    def handle(self,*args,**options):
        if not getattr(settings,'STERAK_DESKTOP_MODE',False):
            raise RuntimeError('No ejecutar en Render.')
        self.stdout.write('6E: cola persistente iniciada. Envío desactivado por defecto.')
        while True:
            try:
                reconcile()
                info=enviar_pendientes(limite=20,habilitacion_requerida=True)
                if info['enviados']:
                    self.stdout.write(f"6E: {info['enviados']} eventos confirmados; {info['pendientes']} pendientes.")
            except ReceptorNoListo as exc:
                # Sin Internet no se pierden datos; evita mostrar credenciales.
                self.stderr.write('6E: '+str(exc)[:190])
            except Exception as exc:
                self.stderr.write('6E: error local de cola ('+exc.__class__.__name__+').')
            time.sleep(120)
