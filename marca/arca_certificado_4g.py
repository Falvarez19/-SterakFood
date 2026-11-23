"""SterakFood 4G: diagnóstico del certificado P12, solo lectura.

Nunca entrega certificados, claves privadas, passwords, datos X.509 personales,
ni tokens. Solo devuelve estados de disponibilidad/vigencia.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone


def _vigencia(cert, ahora=None):
    ahora = ahora or datetime.now(timezone.utc)
    inicio = getattr(cert, 'not_valid_before_utc', None)
    fin = getattr(cert, 'not_valid_after_utc', None)
    if inicio is None:
        inicio = cert.not_valid_before.replace(tzinfo=timezone.utc)
    if fin is None:
        fin = cert.not_valid_after.replace(tzinfo=timezone.utc)
    if ahora < inicio:
        return {'estado': 'error', 'detalle': 'El certificado aún no es válido. Revisá su fecha de inicio.'}
    if ahora >= fin:
        return {'estado': 'error', 'detalle': 'El certificado digital venció. Es necesario renovarlo.'}
    dias = (fin - ahora).days
    vencimiento = fin.strftime('%d/%m/%Y')
    if dias < 30:
        return {'estado': 'aviso', 'detalle': f'P12 válido, pero vence el {vencimiento} (menos de 30 días).'}
    return {'estado': 'ok', 'detalle': f'P12 legible y vigente hasta {vencimiento}. Falta confirmar permisos con WSAA.'}


def inspeccionar_certificado():
    """Solo se ejecuta desde la vista del propietario de 4F.

    _credentials() centraliza la apertura del P12 y maneja la clave en el backend.
    No se reimplementa ni cambia el mecanismo de secretos de SterakFood.
    """
    if not os.environ.get('ARCA_P12_BASE64', '').strip():
        return {'estado': 'pendiente', 'detalle': 'No hay certificado P12 configurado en los secretos del servidor.'}
    try:
        from pedidos.arca_wsfe import _credentials
        _clave, cert = _credentials()
        return _vigencia(cert)
    except Exception:
        return {'estado': 'error', 'detalle': 'No se pudo abrir o validar el P12. Revisá su formato, contraseña y vigencia en el servidor.'}
