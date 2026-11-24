"""Pruebas puras de la simulación 5D. No usan certificado ni ARCA."""
import unittest
from xml.etree import ElementTree as ET
from .arca_factura_c_5d import (
    preparar_ejemplo_c, preparar_nodo_wsfe_c, SimulacionCError,
)


class FacturaCTest(unittest.TestCase):
    def _tags(self, xml):
        return {node.tag.rsplit('}', 1)[-1]: node.text for node in xml.iter()}

    def test_tipo_c_sin_iva_discriminado(self):
        datos = preparar_ejemplo_c('1210.00', punto_venta=4, numero=7, fecha='20261124')
        tags = self._tags(preparar_nodo_wsfe_c(datos))
        self.assertEqual(tags['CbteTipo'], '11')
        self.assertEqual(tags['PtoVta'], '4')
        self.assertEqual(tags['ImpTotal'], '1210.00')
        self.assertEqual(tags['ImpNeto'], '1210.00')
        self.assertEqual(tags['ImpIVA'], '0.00')
        self.assertEqual(tags['CondicionIVAReceptorId'], '5')
        root = preparar_nodo_wsfe_c(datos)
        self.assertNotIn('AlicIva', [n.tag.rsplit('}',1)[-1] for n in root.iter()])
        self.assertNotIn('Auth', [n.tag.rsplit('}',1)[-1] for n in root.iter()])

    def test_rechaza_importes_inseguros(self):
        for value in ('0', '-2', '123.456', '1e9', '', '1/2', '100000000', '1,000.50'):
            with self.subTest(value=value), self.assertRaises(SimulacionCError):
                preparar_ejemplo_c(value)

    def test_no_persiste_ni_llama_a_red(self):
        datos = preparar_ejemplo_c('30,50')
        self.assertEqual(datos.importe_total, datos.importe_neto)
        self.assertEqual(datos.importe_iva, 0)
        self.assertEqual(datos.tipo_comprobante, 11)

    def test_fecha_invalida(self):
        with self.assertRaises(SimulacionCError):
            preparar_ejemplo_c('100.00', fecha='20261302')


if __name__ == '__main__':
    unittest.main()
