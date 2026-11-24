"""Vista de simulación Factura C: exclusiva propietario, sin emitir ni persistir."""
from __future__ import annotations

from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from pedidos.arca_factura_c_5d import preparar_ejemplo_c, preparar_nodo_wsfe_c, SimulacionCError
from .views import autorizado


@never_cache
@csrf_protect
@require_POST
def simular_factura_c_5d(request):
    if not autorizado(request):
        return HttpResponseForbidden('Acceso exclusivo del propietario.')
    try:
        importe = (request.POST.get('importe') or '').strip()
        # Siempre ejemplo controlado. No consulta credenciales ni datos fiscales;
        # el punto de venta 1 y número 1 NO son reservas ni numeración real.
        ejemplo = preparar_ejemplo_c(importe, punto_venta=1, numero=1)
        preparar_nodo_wsfe_c(ejemplo)
        messages.success(request,
            f'Simulación Factura C: tipo 11, total $ {ejemplo.importe_total:.2f}, '
            'IVA discriminado $ 0.00, sin CAE. No se enviaron datos a ARCA '
            'ni se modificó la numeración fiscal.')
    except SimulacionCError as exc:
        messages.error(request, str(exc))
    return redirect('marca:arca_propietario')
