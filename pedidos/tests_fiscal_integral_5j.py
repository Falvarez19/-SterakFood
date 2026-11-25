from decimal import Decimal
from django.test import SimpleTestCase
from pedidos.fiscal_integral_5j import _receptor, calcular, armar_solicitud
from pedidos.arca_wsfe import _value

class FacturacionIntegralTests(SimpleTestCase):
    def test_c_sin_iva(self):
        d=calcular(Decimal('121.00'),11)
        self.assertEqual(d['iva'],Decimal('0.00'))
        self.assertEqual(d['neto'],Decimal('121.00'))
    def test_ab_iva21(self):
        d=calcular(Decimal('121.00'),6)
        self.assertEqual(d['neto'],Decimal('100.00'))
        self.assertEqual(d['iva'],Decimal('21.00'))
    def test_mono_c(self):
        rec=_receptor({'condicion_receptor':'consumidor_final'},'monotributo',Decimal('10'))
        self.assertEqual(rec['tipo'],11)
    def test_a_necessita_cuit(self):
        with self.assertRaises(Exception):
            _receptor({'condicion_receptor':'responsable_inscripto','numero_documento':'123'},'ri',Decimal('21'))
    def test_soap_c_no_iva(self):
        r=_receptor({'condicion_receptor':'consumidor_final'},'monotributo',Decimal('100'))
        xml=armar_solicitud('t','s','20123456786',5,11,4,'20261124',Decimal('100'),r)
        self.assertEqual(_value(xml,'CbteTipo'),'11')
        self.assertEqual(_value(xml,'CondicionIVAReceptorId'),'5')
        self.assertFalse(any(n.tag.endswith('AlicIva') for n in xml.iter()))
    def test_soap_a_iva(self):
        r={'tipo':1,'doc_tipo':80,'doc_nro':'20123456786','iva_receptor':1,'nombre':'Empresa'}
        xml=armar_solicitud('t','s','20123456786',5,1,4,'20261124',Decimal('121'),r)
        self.assertEqual(_value(xml,'ImpIVA'),'21.00')
        self.assertTrue(any(n.tag.endswith('AlicIva') for n in xml.iter()))
