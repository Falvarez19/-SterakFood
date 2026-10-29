"""Regresión del panel de cuentas corrientes embebido en el Salón POS."""
from django.test import TestCase
from django.urls import reverse


class CuentasDentroDelSalonTests(TestCase):
    def setUp(self):
        session = self.client.session
        session['dashboard_auth'] = True
        session.save()

    def test_fragmento_ajax_muestra_cuentas_sin_iframe(self):
        url = reverse('pedidos:cuentas_ventana_salon')
        res = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res.status_code, 200)
        html = res.content.decode('utf-8')
        self.assertIn('id="tab-cuentas"', html)
        self.assertIn('cuentas-buscar', html)
        self.assertNotIn('<iframe', html.lower())

    def test_cuentas_no_embebidas_sigue_disponible(self):
        res = self.client.get(reverse('pedidos:cuentas_ventana_salon'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'id="tab-cuentas"')

    def test_salon_tiene_contenedor_sin_iframe_cuentas(self):
        res = self.client.get(reverse('pedidos:salon'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'id="sc-dialog-content"')
        self.assertNotContains(res, 'id="sc-dialog-frame"')

    def test_sin_sesion_no_expone_cuentas(self):
        self.client.logout()
        res = self.client.get(reverse('pedidos:cuentas_ventana_salon'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertNotEqual(res.status_code, 200)
