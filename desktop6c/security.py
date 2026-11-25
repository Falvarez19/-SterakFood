"""Utilidades simples, para un único local por instalación."""
import base64
import hashlib
import ipaddress
import os
import re
import socket
from urllib.parse import urlsplit

from cryptography.fernet import Fernet
from django.conf import settings

TOKEN_RE = re.compile(r'^[A-Za-z0-9_-]{30,128}$')


def token_hash(raw):
    return hashlib.sha256(raw.encode('ascii')).hexdigest()


def _cipher():
    # SECRET_KEY es exclusivo del Desktop y se conserva fuera del repositorio.
    digest = hashlib.sha256(settings.SECRET_KEY.encode('utf-8')).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_token(raw):
    if not TOKEN_RE.fullmatch(raw):
        raise ValueError('Clave de vinculación inválida.')
    return _cipher().encrypt(raw.encode('ascii')).decode('ascii')


def decrypt_token(cipher):
    return _cipher().decrypt(cipher.encode('ascii')).decode('ascii')


def clean_server_url(raw):
    """Solo HTTPS de Internet pública, nunca localhost/LAN ni URL con credenciales."""
    value = (raw or '').strip().rstrip('/')
    parts = urlsplit(value)
    if parts.scheme != 'https' or parts.username or parts.password or parts.query or parts.fragment or parts.path not in ('', '/'):
        raise ValueError('Ingresá la URL HTTPS principal del sitio, sin rutas ni parámetros.')
    host = (parts.hostname or '').lower().rstrip('.')
    if not host or len(host) > 253 or '.' not in host or parts.port not in (None, 443):
        raise ValueError('El dominio de Render debe ser público y usar HTTPS.')
    if host.endswith(('.local', '.internal', '.localhost', '.test', '.invalid', '.example')):
        raise ValueError('El dominio no es válido para la vinculación.')
    try:
        ipaddress.ip_address(host)
        raise ValueError('Ingresá un dominio público, no una dirección IP.')
    except ValueError as exc:
        if str(exc).startswith('Ingresá un dominio'):
            raise
    if not re.fullmatch(r'[A-Za-z0-9.-]+', host) or '..' in host:
        raise ValueError('Dominio inválido.')
    # Defensa adicional contra enlaces a redes privadas, incluso con un FQDN.
    try:
        addresses = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
    except OSError as exc:
        raise ValueError('No se pudo resolver el dominio del sitio.') from exc
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError('El dominio apunta a una dirección no pública.')
    return 'https://' + host
