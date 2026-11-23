"""Paso 4E: solo el propietario puede consultar y cambiar datos fiscales.

Ejecutar: python manage.py test marca.tests_arca_propietario_4e
No crea facturas ni utiliza certificados reales.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from pedidos.models import ConfiguracionFiscal


class SeguridadFiscalPropietarioTests(TestCase):
    def setUp(self):
        model = get_user_model()
        self.dueno = model.objects.create_superuser(username='dueno_prueba', password='PruebaMuyLarga!123', email='')
        self.cajero = model.objects.create_user(username='cajero_prueba', password='PruebaMuyLarga!124', email='')
        self.url = reverse('marca:arca_propietario')

    def test_anonymous_no_ve_fiscal(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(b'CUIT (11', response.content)

    def test_cajero_no_ve_fiscal_aunque_tenga_pin_dashboard(self):
        self.client.force_login(self.cajero)
        session = self.client.session
        session['dashboard_auth'] = True
        session.save()
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.assertFalse(ConfiguracionFiscal.objects.exists())

    def test_cajero_no_puede_grabar(self):
        self.client.force_login(self.cajero)
        self.client.post(self.url, {'razon_social': 'Cambiado'})
        self.assertFalse(ConfiguracionFiscal.objects.exists())

    def test_superusuario_ve_y_graba_datos_no_secretos(self):
        self.client.force_login(self.dueno)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.client.post(self.url, {
            'razon_social': 'Restaurante prueba', 'cuit': '',
            'condicion_iva': 'monotributo', 'punto_venta_referencia': '5',
            'domicilio_fiscal': 'Domicilio de prueba',
        })
        row = ConfiguracionFiscal.objects.get(pk=1)
        self.assertEqual(row.razon_social, 'Restaurante prueba')
        self.assertEqual(row.punto_venta_referencia, 5)

    def test_original_fiscal_preparacion_protegido_del_pin(self):
        self.client.force_login(self.cajero)
        session = self.client.session
        session['dashboard_auth'] = True
        session.save()
        self.assertEqual(self.client.get(reverse('pedidos:fiscal_preparacion')).status_code, 302)
