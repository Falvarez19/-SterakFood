"""Pruebas de la configuracion sin alterar ventas ni cuentas corrientes."""
import json
from django.test import TestCase
from django.urls import reverse
from .models import Configuracion, Mozo


class ConfiguracionOperativaTests(TestCase):
    def habilitar_panel(self):
        session = self.client.session
        session['dashboard_auth'] = True
        session.save()

    def test_pantalla_requiere_sesion(self):
        url = reverse('pedidos:configuracion_operativa')
        self.assertEqual(self.client.get(url).status_code, 302)
        self.habilitar_panel()
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_cambiar_mesas_no_borra_mozos(self):
        self.habilitar_panel()
        Mozo.objects.create(nombre='Marcelo')
        respuesta = self.client.post(reverse('pedidos:guardar_mesas_visibles'),
            data=json.dumps({'numero_mesas_visibles': 24}),
            content_type='application/json')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Configuracion.objects.get(pk=1).numero_mesas_visibles, 24)
        self.assertEqual(Mozo.objects.count(), 1)
        salon = self.client.get(reverse('pedidos:salon'))
        self.assertEqual(salon.status_code, 200)
        self.assertEqual(list(salon.context['mesas']), list(range(1,25)))

    def test_cantidad_invalida_no_se_guarda(self):
        self.habilitar_panel()
        for valor in [0, 101, -1, 'dos', True, 1.5]:
            respuesta = self.client.post(reverse('pedidos:guardar_mesas_visibles'),
                data=json.dumps({'numero_mesas_visibles': valor}),
                content_type='application/json')
            self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(Configuracion.objects.filter(numero_mesas_visibles__lt=1).exists())

    def test_modificar_mesas_no_autorizado(self):
        self.assertEqual(self.client.post(reverse('pedidos:guardar_mesas_visibles'),
            data='{"numero_mesas_visibles": 20}', content_type='application/json').status_code, 403)
