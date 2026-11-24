"""Pruebas 5G: ninguna test solicita CAE ni realiza llamadas de red."""
from xml.etree import ElementTree as ET
from django.test import SimpleTestCase
from pedidos.arca_c_consulta_5g import (
    armar_ultimo_c, leer_ultimo_c, ConsultaFacturaCError,
)

class PreflightFacturaCTests(SimpleTestCase):
    def test_consulta_tipo_11_y_sin_emision(self):
        root = armar_ultimo_c('token-falso', 'firma-falsa', '20123456789', 5)
        xml = ET.tostring(root, encoding='unicode')
        self.assertIn('FECompUltimoAutorizado', xml)
        self.assertIn('<ns0:CbteTipo>11</ns0:CbteTipo>', xml)
        self.assertNotIn('FECAESolicitar', xml)
        self.assertNotIn('FECAEDetRequest', xml)

    def test_produccion_se_rechaza(self):
        with self.assertRaises(ConsultaFacturaCError):
            armar_ultimo_c('t', 's', '20123456789', 5, entorno='produccion')

    def test_respuesta_ultimo_numero_valida(self):
        root = ET.fromstring('''<Envelope><Body><FECompUltimoAutorizadoResponse>
          <FECompUltimoAutorizadoResult><CbteNro>25</CbteNro></FECompUltimoAutorizadoResult>
        </FECompUltimoAutorizadoResponse></Body></Envelope>''')
        self.assertEqual(leer_ultimo_c(root), 25)

    def test_respuesta_soap_error_no_aceptada(self):
        root = ET.fromstring('<Envelope><Fault><faultstring>error</faultstring></Fault></Envelope>')
        with self.assertRaises(ConsultaFacturaCError):
            leer_ultimo_c(root)

    def test_respuesta_errors_no_aceptada(self):
        root = ET.fromstring('''<Envelope><FECompUltimoAutorizadoResult>
         <CbteNro>13</CbteNro><Errors><Err><Code>100</Code></Err></Errors>
        </FECompUltimoAutorizadoResult></Envelope>''')
        with self.assertRaises(ConsultaFacturaCError):
            leer_ultimo_c(root)
