"""Piloto Desktop: servidor Django SOLO en loopback + sincronizador periódico."""
import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


def port_open(port):
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=0.4):
            return True
    except OSError:
        return False


def main():
    root = Path(__file__).resolve().parent.parent
    manage = str(root / 'manage.py')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'SisPedidos.settings_desktop'
    port = 8765
    if port_open(port):
        print('Puerto 8765 ocupado. No se iniciará otra copia. Verificá que sea tu SterakFood Desktop.')
        return 1
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = 'SisPedidos.settings_desktop'
    cmd = [sys.executable, manage]
    server = subprocess.Popen(cmd + ['runserver', '127.0.0.1:8765', '--noreload'], cwd=str(root), env=env)
    sync = subprocess.Popen(cmd + ['desktop_sync_loop'], cwd=str(root), env=env)
    # STERAKFOOD_6D_PRINTER_START
    printer = subprocess.Popen(cmd + ['desktop_print_loop'], cwd=str(root), env=env)
    try:
        for _ in range(40):
            if server.poll() is not None:
                print('El servidor local no pudo iniciar. Revisá el error de Django.')
                return 2
            if port_open(port):
                break
            time.sleep(.25)
        else:
            print('El servidor no respondió. Revisá los mensajes.')
            return 3
        webbrowser.open('http://127.0.0.1:8765/desktop/')
        print('SterakFood Desktop ejecutándose localmente. Cerrá esta ventana para terminar.')
        return server.wait()
    except KeyboardInterrupt:
        print('Cerrando SterakFood Desktop...')
        return 0
    finally:
        for child in (printer, sync, server):
            if child.poll() is None:
                child.terminate()
        for child in (printer, sync, server):
            try: child.wait(timeout=3)
            except subprocess.TimeoutExpired: child.kill()


if __name__ == '__main__':
    sys.exit(main())
