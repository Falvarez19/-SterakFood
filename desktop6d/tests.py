"""Pruebas sin hardware ni conexión ARCA."""
from decimal import Decimal
from django.test import SimpleTestCase
from types import SimpleNamespace
from .printing import _sin_importes, _raw
from .views import _ip_local


class Offline6DTests(SimpleTestCase):
    def test_opciones_cocina_sin_importes(self):
        self.assertEqual(_sin_importes('Napolitana (+2500)'), 'Napolitana')

    def test_ticket_no_fiscal(self):
        self.assertIn(b'NO VALIDO COMO FACTURA', _raw(['NO VALIDO COMO FACTURA']))

    def test_ip_solo_privada(self):
        self.assertEqual(_ip_local('192.168.1.20'), '192.168.1.20')
        with self.assertRaises(ValueError): _ip_local('8.8.8.8')
