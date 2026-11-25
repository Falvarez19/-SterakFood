"""Pruebas que el desarrollador puede ejecutar luego de instalar Django."""
from django.test import SimpleTestCase
from .sync import _validate


class CatalogValidationTests(SimpleTestCase):
    def sample(self):
        return {
            'schema': 1,
            'installation_id': '11111111-1111-4111-8111-111111111111',
            'categorias': [{'id': 3, 'nombre': 'Bebidas'}],
            'puestos': [{'id': 1, 'nombre': 'Barra', 'slug': 'barra', 'telefono': '111', 'abierto': True}],
            'productos': [{
                'id': 17, 'categoria_id': 3, 'puestos': [1], 'nombre': 'Agua',
                'codigo': '001', 'descripcion': '', 'precio': '2000.00',
                'disponible': True, 'promocion': False, 'orden': 1,
                'foto_revision': '', 'variantes': '', 'guarniciones': '',
                'puntos_coccion': '', 'rellenos': '', 'salsas': '',
                'adicionales': '', 'opcion_hielo': '',
            }],
        }

    def test_valid_snapshot(self):
        self.assertTrue(_validate(self.sample()))

    def test_reject_duplicate_product_id(self):
        data = self.sample()
        data['productos'].append(dict(data['productos'][0]))
        with self.assertRaises(ValueError):
            _validate(data)

    def test_reject_invalid_price(self):
        data = self.sample()
        data['productos'][0]['precio'] = '-1'
        with self.assertRaises(ValueError):
            _validate(data)

    def test_reject_cross_category(self):
        data = self.sample()
        data['productos'][0]['categoria_id'] = 999
        with self.assertRaises(ValueError):
            _validate(data)
