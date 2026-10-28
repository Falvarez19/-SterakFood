"""Pruebas sin Django ni conexiones a ARCA; casos SOAP simulados."""
import sys, types, unittest, pathlib
from unittest.mock import patch
from decimal import Decimal
from xml.etree import ElementTree as ET

# Stubs mínimos para probar el cliente SOAP sin ejecutar Django/Render.
django=types.ModuleType('django');django.__path__=[]
conf=types.ModuleType('django.conf');conf.settings=types.SimpleNamespace()
core=types.ModuleType('django.core');core.__path__=[]
cache=types.ModuleType('django.core.cache');cache.cache=types.SimpleNamespace(get=lambda *_:None,set=lambda *_ ,**__:None)
sys.modules.update({'django':django,'django.conf':conf,'django.core':core,'django.core.cache':cache})
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'SisteMaSM'))
from pedidos import arca_wsfe as ws

class ArcaOfflineTests(unittest.TestCase):
    def test_qr_codifica_comprobante(self):
        import base64,json
        u=ws.url_qr('20123456789',5,25887,'20261027',Decimal('7000.00'),'12345098765432')
        self.assertTrue(u.startswith('https://www.arca.gob.ar/fe/qr/?p='))
        x=json.loads(base64.b64decode(u.split('?p=')[1]))
        self.assertEqual(x['ptoVta'],5)
        self.assertEqual(x['nroCmp'],25887)
        self.assertEqual(x['codAut'],12345098765432)
    def test_env_produccion_protegida(self):
        with patch.dict('os.environ',{'ARCA_FISCAL_ENABLED':'1','ARCA_ENV':'produccion'},clear=True):
            with self.assertRaises(ws.ArcaError):ws._environment()
        with patch.dict('os.environ',{'ARCA_FISCAL_ENABLED':'1','ARCA_ENV':'homologacion'},clear=True):
            self.assertEqual(ws._environment(),'homologacion')
    def test_solicitud_xml_iva_y_confirmacion(self):
        retorno=ET.fromstring('''<Envelope><FeCabResp><Resultado>A</Resultado></FeCabResp><FeDetResp><FECAEDetResponse><Resultado>A</Resultado><CAE>12345678901234</CAE><CAEFchVto>20261105</CAEFchVto></FECAEDetResponse></FeDetResp></Envelope>''')
        seen=[]
        def fake_post(url,action,element): seen.append(ET.tostring(element).decode());return retorno
        with patch.object(ws,'_environment',return_value='homologacion'), patch.object(ws,'_get_token',return_value=('X','Y','20123456789')),patch.object(ws,'_soap_post',side_effect=fake_post):
            result=ws.emitir_factura_b(5,25887,Decimal('7000.00'),'20261027')
        self.assertEqual(result['cae'],'12345678901234')
        self.assertEqual(Decimal(result['neto'])+Decimal(result['iva']),Decimal('7000.00'))
        self.assertIn('CondicionIVAReceptorId',seen[0]);self.assertIn('DocTipo',seen[0]);self.assertIn('FECAESolicitar',seen[0]);self.assertIn('AlicIva',seen[0]);self.assertIn('CbteDesde',seen[0])
    def test_solicitud_rechazada_no_devuelve_cae(self):
        retorno=ET.fromstring('''<Envelope><FeDetResp><FECAEDetResponse><Resultado>R</Resultado><CAE></CAE><Observaciones><Obs><Code>10000</Code><Msg>Rechazada</Msg></Obs></Observaciones></FECAEDetResponse></FeDetResp></Envelope>''')
        with patch.object(ws,'_environment',return_value='homologacion'),patch.object(ws,'_get_token',return_value=('X','Y','20123456789')),patch.object(ws,'_soap_post',return_value=retorno):
            with self.assertRaises(ws.ArcaError):ws.emitir_factura_b(5,25887,'7000.00','20261027')
    def test_respuesta_incierta_no_duplicar(self):
        with patch.object(ws,'_environment',return_value='homologacion'),patch.object(ws,'_get_token',return_value=('X','Y','20123456789')),patch.object(ws,'_soap_post',side_effect=ws.ArcaIncierto('Sin respuesta')):
            with self.assertRaises(ws.ArcaIncierto):ws.emitir_factura_b(5,1,'100.00','20261027')
    def test_consultar_cae(self):
        retorno=ET.fromstring('''<Envelope><ResultGet><CodAutorizacion>12345678901234</CodAutorizacion><ImpTotal>7000.00</ImpTotal><CbteFch>20261027</CbteFch><FchVto>20261105</FchVto></ResultGet></Envelope>''')
        with patch.object(ws,'_environment',return_value='homologacion'),patch.object(ws,'_get_token',return_value=('X','Y','20123456789')),patch.object(ws,'_soap_post',return_value=retorno):
            self.assertEqual(ws.consultar(5,6,25887)['cae'],'12345678901234')

if __name__=='__main__':unittest.main()
