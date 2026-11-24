"""SterakFood 5B: prueba segura de bóveda; no consulta ARCA ni emite facturas.

Uso exclusivo del propietario, con CSRF. Cifra y descifra un dato aleatorio en
memoria y hace una lectura mínima de la tabla de credenciales.
"""
from __future__ import annotations

import secrets

from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from .views import autorizado
from .arca_vault_5a import _fernet, ConfiguracionSeguraError
from .models import ArcaCredencial


@never_cache
@csrf_protect
@require_POST
def comprobar_boveda_5b(request):
    if not autorizado(request):
        return HttpResponseForbidden('Acceso exclusivo del propietario.')
    try:
        fernet = _fernet()
        muestra = secrets.token_bytes(32)
        token = fernet.encrypt(muestra)
        if fernet.decrypt(token) != muestra:
            raise ConfiguracionSeguraError('La prueba de cifrado no pasó.')
        # Solo lectura. No crea, modifica ni descarga ningún certificado.
        ArcaCredencial.objects.exists()
    except ConfiguracionSeguraError:
        messages.error(request, 'Bóveda no disponible. Revisá STERAK_ARCA_VAULT_KEY en el servidor.')
    except Exception:
        # No mostrar trazas de BD, URLs ni otros secretos al propietario.
        messages.error(request, 'El cifrado funciona, pero no se pudo verificar el acceso a la base de datos de la bóveda.')
    else:
        messages.success(request, 'Bóveda lista: clave válida, cifrado reversible y tabla de credenciales accesible. No se utilizó ningún certificado ni se emitieron facturas.')
    return redirect('marca:arca_propietario')
