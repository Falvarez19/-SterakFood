"""Configuracion diaria por INSTALACION de SterakFood.

No administra ventas ni cambia el motor de impresion. Reutiliza los modelos
Mozo y ConfiguracionImpresorasPOS para evitar listas duplicadas por cliente.
"""
import json
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from .models import Configuracion, Mozo


def _configuracion():
    configuracion, _ = Configuracion.objects.get_or_create(pk=1)
    return configuracion


def configuracion_operativa(request):
    """Vista de trabajo: mesas visibles, empleados y las impresoras existentes."""
    if not request.session.get('dashboard_auth'):
        return redirect(reverse('pedidos:login_dashboard'))
    config = _configuracion()
    return render(request, 'pedidos/configuracion_operativa.html', {
        'cantidad_mesas_visibles': config.numero_mesas_visibles,
        'mozos_operativos': Mozo.objects.all().order_by('nombre'),
    })


@require_POST
def guardar_mesas_visibles(request):
    """Cambiar SOLO la grilla de mesas; nunca elimina cuentas locales ni QR.

    Se mantiene el rango 1..100 del motor original. Una mesa fuera de la grilla
    sigue accesible mediante Mesa rapida, por ejemplo ante consumos previos.
    """
    if not request.session.get('dashboard_auth'):
        return JsonResponse({'status': 'error', 'mensaje': 'No autorizado'}, status=403)
    try:
        data = json.loads(request.body.decode('utf-8'))
        valor = data.get('numero_mesas_visibles')
        if isinstance(valor, bool) or not str(valor).isdigit():
            raise ValueError('Ingresá una cantidad entera de mesas.')
        numero = int(valor)
        if numero < 1 or numero > 100:
            raise ValueError('Elegí entre 1 y 100 mesas.')
    except (ValueError, TypeError, UnicodeError) as exc:
        return JsonResponse({'status': 'error', 'mensaje': str(exc) or 'Dato inválido'}, status=400)
    config = _configuracion()
    config.numero_mesas_visibles = numero
    config.save(update_fields=['numero_mesas_visibles'])
    return JsonResponse({
        'status': 'ok', 'numero_mesas_visibles': numero,
        'mensaje': 'Grilla actualizada. Al volver a Salón se mostrará la nueva cantidad.',
    })
