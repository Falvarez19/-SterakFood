"""Descubrimiento SOLO de colas instaladas en Windows.

USB/Ethernet/Wi-Fi: Windows puede mostrar impresoras de cualquiera de esos
transportes, pero una cola WSD/IP no permite distinguir con certeza Wi-Fi.
No barre la red, no abre impresoras y nunca imprime tickets.
"""
from __future__ import annotations

import json
import os
import subprocess


def _clase_puerto(port):
    txt = (port or '').upper()
    if any(p in txt for p in ('USB', 'LPT', 'COM')):
        return 'USB / local'
    if any(p in txt for p in ('IP_', 'WSD-', 'TCP', '192.168.', '10.', '172.', '\\\\')):
        return 'Red / Wi-Fi'
    return 'Windows'


def impresoras_instaladas():
    """Devuelve lista de {nombre, puerto, conexion} sin información sensible."""
    if os.name != 'nt':
        return [], 'La detección automática solo está disponible en Windows.'
    items = []
    error = ''
    try:
        import win32print
        flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        for p in win32print.EnumPrinters(flags):
            name = str(p[2] or '').strip()
            if not name:
                continue
            port = ''
            try:
                handle = win32print.OpenPrinter(name)
                try:
                    info = win32print.GetPrinter(handle, 2)
                    port = str(info.get('pPortName') or '')
                finally:
                    win32print.ClosePrinter(handle)
            except Exception:
                pass
            items.append({'nombre': name[:120], 'puerto': port[:80], 'conexion': _clase_puerto(port)})
    except ImportError:
        error = 'pywin32 no instalado: se usará la búsqueda de Windows.'
    except Exception as exc:
        error = 'Windows no permitió consultar pywin32: '+type(exc).__name__

    # PowerShell trabaja sin pywin32. Es lectura local, sin red ni descargas.
    if not items:
        try:
            script = ("Get-CimInstance -ClassName Win32_Printer | "
                      "Select-Object Name,PortName,Network,Local | ConvertTo-Json -Compress")
            proc = subprocess.run(
                ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script],
                capture_output=True, timeout=12,
            )
            if proc.returncode != 0:
                raise RuntimeError('No se pudo consultar el catálogo de impresoras de Windows.')
            raw = proc.stdout.decode('utf-8-sig', errors='replace').strip()
            values = json.loads(raw) if raw else []
            if isinstance(values, dict):
                values = [values]
            for p in values:
                if not isinstance(p, dict):
                    continue
                name = str(p.get('Name') or '').strip()
                if not name:
                    continue
                port = str(p.get('PortName') or '')
                items.append({'nombre': name[:120], 'puerto': port[:80],
                              'conexion': _clase_puerto(port)})
            error = ''
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired):
            error = 'Windows no permitió enumerar impresoras. Podés escribir el nombre manualmente.'
    distinct = {p['nombre'].casefold(): p for p in items if p['nombre']}
    return sorted(distinct.values(), key=lambda p: p['nombre'].casefold()), error
