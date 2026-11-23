"""SterakFood 4G: pruebas locales sin ARCA ni secretos reales."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from django.test import SimpleTestCase
from django.urls import reverse
from marca.arca_certificado_4g import _vigencia, inspeccionar_certificado


class CertificadoSimulado:
    def __init__(self, empieza, termina):
        self.not_valid_before_utc = empieza
        self.not_valid_after_utc = termina


class Certificado4GTests(SimpleTestCase):
    def test_falta_p12(self):
        with patch.dict('os.environ', {'ARCA_P12_BASE64': ''}):
            self.assertEqual(inspeccionar_certificado()['estado'], 'pendiente')

    def test_p12_vigente(self):
        ahora = datetime.now(timezone.utc)
        p12 = CertificadoSimulado(ahora-timedelta(days=1), ahora+timedelta(days=120))
        self.assertEqual(_vigencia(p12, ahora)['estado'], 'ok')

    def test_p12_cerca_de_vencer(self):
        ahora = datetime.now(timezone.utc)
        p12 = CertificadoSimulado(ahora-timedelta(days=1), ahora+timedelta(days=3))
        self.assertEqual(_vigencia(p12, ahora)['estado'], 'aviso')

    def test_p12_vencido(self):
        ahora = datetime.now(timezone.utc)
        p12 = CertificadoSimulado(ahora-timedelta(days=120), ahora-timedelta(days=1))
        self.assertEqual(_vigencia(p12, ahora)['estado'], 'error')

    def test_p12_no_legible_no_publica_excepciones(self):
        with patch.dict('os.environ', {'ARCA_P12_BASE64': 'secreto'}):
            with patch('pedidos.arca_wsfe._credentials', side_effect=ValueError('secreto interno')):
                resultado = inspeccionar_certificado()
        self.assertEqual(resultado['estado'], 'error')
        self.assertNotIn('secreto interno', str(resultado))

    def test_endpoint_solo_propietario(self):
        self.assertEqual(self.client.post(reverse('marca:arca_diagnosticar')).status_code, 403)

    @patch('marca.arca_diagnostico_4f.autorizado', return_value=True)
    @patch('marca.arca_diagnostico_4f._fedummy', return_value={
        'disponible': True, 'estados': {'AppServer': 'OK', 'DbServer': 'OK', 'AuthServer': 'OK'}})
    @patch('marca.arca_diagnostico_4f.inspeccionar_certificado', return_value={
        'estado': 'pendiente', 'detalle': 'P12 pendiente'})
    @patch.dict('os.environ', {'ARCA_ENV': 'homologacion', 'ARCA_CUIT': '', 'ARCA_P12_BASE64': '', 'ARCA_PUNTO_VENTA': ''})
    def test_4f_muestra_estado_certificado_sin_emitir(self, cert, dummy, owner):
        result = self.client.post(reverse('marca:arca_diagnosticar'))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['pasos']['certificado']['estado'], 'pendiente')
        self.assertFalse(result.json()['comprobante_emitido'])
