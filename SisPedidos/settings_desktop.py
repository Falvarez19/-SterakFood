"""Configuración Desktop: SIEMPRE SQLite local, aunque haya DATABASE_URL de Render."""
import hashlib
import json
import os
import secrets
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASE_PROFILE = Path(os.environ.get('LOCALAPPDATA') or (Path.home() / '.local' / 'share'))
PROFILE_ID = hashlib.sha256(str(PROJECT_ROOT.resolve()).casefold().encode('utf-8')).hexdigest()[:16]
DATA_DIR = BASE_PROFILE / 'SterakFood' / 'Desktop' / PROFILE_ID
DATA_DIR.mkdir(parents=True, exist_ok=True)
SECRET_FILE = DATA_DIR / 'secret.key'
if not SECRET_FILE.exists():
    with SECRET_FILE.open('x', encoding='ascii') as f:
        f.write(secrets.token_urlsafe(60))
try:
    SECRET_DESKTOP = SECRET_FILE.read_text(encoding='ascii').strip()
except OSError as exc:
    raise RuntimeError('No se puede leer la clave local del Desktop.') from exc
if len(SECRET_DESKTOP) < 50:
    raise RuntimeError('La clave local no cumple el tamaño mínimo.')
os.environ['SECRET_KEY'] = SECRET_DESKTOP

from .settings import *  # noqa: F401,F403,E402

SECRET_KEY = SECRET_DESKTOP
DEBUG = False
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:8765', 'http://localhost:8765']
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': DATA_DIR / 'desktop.sqlite3', 'OPTIONS': {'timeout': 20}}}
MEDIA_ROOT = str(DATA_DIR / 'media')
STATIC_ROOT = str(DATA_DIR / 'staticfiles')
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = None
ARCA_FISCAL_ENABLED = False
STERAK_DESKTOP_MODE = True
# STERAKFOOD_DESKTOP_6D_LOCAL
SM_LOCAL_MODE = True
DESKTOP_OPERACION_6D = True
if 'desktop6d' not in INSTALLED_APPS:
    INSTALLED_APPS += ['desktop6d']
STATICFILES_DIRS = [p for p in STATICFILES_DIRS if Path(p).is_dir()]

# Las operaciones fiscales no se emiten offline. El operador debe usar la web autorizada.
os.environ['ARCA_FISCAL_ENABLED'] = '0'
LOCAL_CONFIG = DATA_DIR / 'config.json'
if LOCAL_CONFIG.is_file():
    try:
        _local = json.loads(LOCAL_CONFIG.read_text(encoding='utf-8'))
        PANEL_PIN = str(_local.get('panel_pin') or '')
    except (ValueError, OSError):
        PANEL_PIN = ''
else:
    PANEL_PIN = ''
