"""Pantalla de vinculación de propietario (nunca expone secretos guardados)."""
import secrets
import uuid
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseForbidden
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone
from marca.views import autorizado
from .models import DesktopAccessToken, DesktopLink, DesktopSyncEvent
from .security import clean_server_url, encrypt_token, token_hash


def _owner(request):
    return bool(request.user.is_authenticated and request.user.is_active and request.user.is_superuser)


def _desktop_only():
    return getattr(settings, 'STERAK_DESKTOP_MODE', False)


@never_cache
def home(request):
    if not _desktop_only():
        return redirect('desktop6c:web_keys')
    return redirect('desktop6c:pair')


@never_cache
@require_http_methods(['GET', 'POST'])
def web_keys(request):
    if _desktop_only():
        return HttpResponseForbidden('Las claves solo se crean en la web.')
    if not _owner(request):
        return redirect('marca:acceso')
    new_key = None
    error = ''
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            label = (request.POST.get('label') or '').strip()
            if not 2 <= len(label) <= 80:
                error = 'Ingresá un nombre de equipo entre 2 y 80 caracteres.'
            else:
                new_key = secrets.token_urlsafe(36)
                DesktopAccessToken.objects.create(label=label, token_hash=token_hash(new_key))
        elif action == 'revoke':
            try:
                token_id = int(request.POST.get('token_id') or '')
            except ValueError:
                token_id = 0
            DesktopAccessToken.objects.filter(pk=token_id).update(active=False)
    return render(request, 'desktop6c/web_keys.html', {
        'new_key': new_key, 'error': error,
        'tokens': DesktopAccessToken.objects.all().order_by('-created_at')[:50],
    })


@never_cache
@require_http_methods(['GET', 'POST'])
def pair(request):
    if not _desktop_only():
        return HttpResponseForbidden('La vinculación se realiza en Desktop.')
    error = ''
    if not _owner(request):
        form = AuthenticationForm(request=request, data=request.POST if request.POST.get('action') == 'login' else None)
        if request.method == 'POST' and form.is_valid():
            user = form.get_user()
            if user.is_active and user.is_superuser:
                login(request, user)
                return redirect('desktop6c:pair')
            error = 'Esta cuenta no tiene permisos de propietario.'
        return render(request, 'desktop6c/local_login.html', {'form': form, 'error': error})
    link = DesktopLink.objects.first()
    if request.method == 'POST':
        if link:
            error = 'La PC ya está vinculada. Para cambiar de negocio hace falta migración asistida, no se borrarán ventas.'
        else:
            try:
                server = clean_server_url(request.POST.get('server_url'))
                key = (request.POST.get('token') or '').strip()
                from .sync import fetch_snapshot, apply_snapshot
                snapshot = fetch_snapshot(server, key)
                web_id = uuid.UUID(snapshot['installation_id'])
                with transaction.atomic():
                    link = DesktopLink.objects.create(server_url=server, web_instance_id=web_id, token_ciphertext=encrypt_token(key))
                    apply_snapshot(link, snapshot, token=key)
                return redirect('desktop6c:pair')
            except Exception as exc:
                error = f'No se pudo vincular: {str(exc)[:240]}'
    return render(request, 'desktop6c/local_panel.html', {
        'link': link, 'error': error,
        'events': DesktopSyncEvent.objects.all()[:8],
    })


@never_cache
@require_POST
def sync_now(request):
    if not _desktop_only():
        return HttpResponseForbidden('Disponible únicamente en Desktop.')
    if not _owner(request):
        return HttpResponseForbidden('Acceso exclusivo del propietario.')
    from .sync import run_sync
    run_sync()
    return redirect('desktop6c:pair')
