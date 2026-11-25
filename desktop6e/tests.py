"""Pruebas aisladas sin red ni API fiscal."""
from django.test import SimpleTestCase
from .protocol import sha, validar


class Protocolo6ETests(SimpleTestCase):
    def test_evento_igual_digest_igual(self):
        x={'tipo':'venta.salon','origen':'pedido:17','total':'3400.00'}
        self.assertEqual(sha(x),sha(dict(reversed(list(x.items())))))

    def test_valida_evento(self):
        import uuid
        x={'tipo':'venta.salon','origen':'pedido:17','total':'3400.00'}
        paquete={'schema':1,'installation_id':str(uuid.uuid4()),'device_id':str(uuid.uuid4()),
            'event_id':str(uuid.uuid4()),'tipo':'venta.salon','origen':'pedido:17',
            'payload':x,'digest':sha(x)}
        self.assertTrue(validar(paquete))
        paquete['payload']={**x,'total':'9999'}
        with self.assertRaises(ValueError):validar(paquete)
