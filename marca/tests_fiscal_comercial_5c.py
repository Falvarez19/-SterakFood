"""Pruebas sin contacto ARCA: python manage.py test marca.tests_fiscal_comercial_5c"""
from unittest.mock import patch
from django.test import SimpleTestCase
from marca.arca_compatibilidad_5c import resumen_fiscal_5c


class CompatibilidadFiscal5CTests(SimpleTestCase):
    def test_responsable_inscripto_declara_solo_factura_b_restringida(self):
        x = resumen_fiscal_5c('ri')
        self.assertIn('Factura B', x['comprobante'])
        self.assertTrue(x['soportado'])
        self.assertIn('21 %', x['detalle'])

    def test_monotributista_ve_factura_c_pendiente_y_no_puede_emitir(self):
        x = resumen_fiscal_5c('monotributo')
        self.assertIn('Factura C', x['comprobante'])
        self.assertFalse(x['soportado'])

    def test_exento_y_otro_no_habilitados(self):
        for condicion in ('exento', 'otro', ''):
            self.assertFalse(resumen_fiscal_5c(condicion)['soportado'])

    @patch('marca.arca_vault_5a.diagnostico_autogestion_5a', return_value=None)
    @patch('marca.arca_vault_5a.boveda_disponible', return_value=True)
    @patch('marca.arca_diagnostico_4f._fedummy', return_value={
        'disponible': True,
        'estados': {'AppServer': 'OK', 'DbServer': 'OK', 'AuthServer': 'OK'},
    })
    @patch('marca.arca_diagnostico_4f.autorizado', return_value=True)
    def test_diagnostico_sin_certificado_informa_subida_por_mi_negocio(self, owner, ping, vault, row):
        from django.test import Client
        from django.urls import reverse
        response = Client().post(reverse('marca:arca_diagnosticar'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['comprobante_emitido'])
        self.assertEqual(data['pasos']['servidores']['estado'], 'ok')
        self.assertIn('Mi negocio', data['pasos']['certificado']['detalle'])
        self.assertNotIn('ARCA_P12_BASE64', str(data))
