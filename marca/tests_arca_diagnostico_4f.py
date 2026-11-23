"""Tests Paso 4F (sin llamadas externas). python manage.py test marca.tests_arca_diagnostico_4f"""
from unittest.mock import patch
from xml.etree import ElementTree as ET

from django.test import SimpleTestCase
from django.urls import reverse
from marca.arca_diagnostico_4f import _datos_puntos, _punto_valido


class Diagnostico4FTests(SimpleTestCase):
    def setUp(self):
        self.url = reverse('marca:arca_diagnosticar')

    def test_get_no_permitido(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_anonimo_no_puede_probar(self):
        self.assertEqual(self.client.post(self.url).status_code, 403)

    @patch('marca.arca_diagnostico_4f.autorizado', return_value=True)
    @patch.dict('os.environ', {'ARCA_ENV':'homologacion', 'ARCA_CUIT':'', 'ARCA_P12_BASE64':'', 'ARCA_PUNTO_VENTA':''})
    @patch('marca.arca_diagnostico_4f._fedummy', return_value={'disponible':True, 'estados':{'AppServer':'OK','DbServer':'OK','AuthServer':'OK'}})
    def test_sin_certificado_comprueba_servidores_pero_no_emite(self, dummy, owner):
        r = self.client.post(self.url)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data['pasos']['servidores']['estado'], 'ok')
        self.assertEqual(data['pasos']['wsaa']['estado'], 'pendiente')
        self.assertFalse(data['comprobante_emitido'])

    def test_lectura_punto_activo(self):
        xml = ET.fromstring('''<Envelope><Body><FEParamGetPtosVentaResponse><FEParamGetPtosVentaResult>
        <ResultGet><PtoVenta><Nro>5</Nro><EmisionTipo>CAE</EmisionTipo>
        <Bloqueado>N</Bloqueado><FchBaja></FchBaja></PtoVenta></ResultGet>
        </FEParamGetPtosVentaResult></FEParamGetPtosVentaResponse></Body></Envelope>''')
        puntos = _datos_puntos(xml)
        self.assertEqual(len(puntos), 1)
        self.assertEqual(puntos[0]['numero'], 5)
        self.assertTrue(_punto_valido(puntos[0])[0])

    def test_punto_bloqueado_no_es_exito(self):
        self.assertFalse(_punto_valido({'bloqueado':'S','fecha_baja':'','emision':'CAE'})[0])

    @patch('marca.arca_diagnostico_4f.autorizado', return_value=True)
    @patch.dict('os.environ', {'ARCA_ENV':'produccion', 'ARCA_CUIT':'20111111112', 'ARCA_P12_BASE64':'simulado', 'ARCA_PUNTO_VENTA':'5'})
    @patch('marca.arca_diagnostico_4f._fedummy', return_value={'disponible':True, 'estados':{'AppServer':'OK','DbServer':'OK','AuthServer':'OK'}})
    @patch('pedidos.arca_wsfe._get_token', return_value=('test-token', 'test-sign', '20111111112'))
    @patch('marca.arca_diagnostico_4f._puntos_autenticados', return_value=[{'numero':5,'bloqueado':'N','fecha_baja':'','emision':'CAE'}])
    def test_completo_es_solo_lectura(self, points, token, dummy, owner):
        r = self.client.post(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['resultado'], 'ok')
        self.assertFalse(r.json()['comprobante_emitido'])
