"""Regresiones para trasladar el Salón de SM a Sterak sin perder herramientas.

No llama ARCA, servicios externos ni impresoras.
"""
import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from .models import Categoria, Producto, Pedido, OperacionCobroSalon, Configuracion


class IntegracionSalonSterakTests(TestCase):
    def setUp(self):
        self.client = Client()
        sesion = self.client.session
        sesion['dashboard_auth'] = True
        sesion.save()
        Configuracion.objects.create(pk=1, salon_habilitado=True)
        categoria = Categoria.objects.create(nombre='Salon')
        self.producto = Producto.objects.create(
            nombre='Milanesa', precio=Decimal('15000.00'),
            codigo_rapido='777', categoria=categoria, disponible=True,
        )
        self.cobrar = reverse('pedidos:cobrar_mesa_salon')
        self.estado = reverse('pedidos:estado_cobro_salon')
        self.opid = 'operacion-st-20261028-01'
        self.payload = {'mesa': '5', 'tipo_pago': 'debito', 'mozo': 'Gaby',
                        'operacion_id': self.opid, 'modo_fiscal': False,
                        'items': [{'producto_id': self.producto.pk,
                                   'codigo': '777', 'nombre': 'Milanesa',
                                   'cantidad': 1, 'precio': 15000}]}

    def test_antes_de_cobrar_no_confirma_la_operacion(self):
        respuesta = self.client.get(self.estado, {'operacion_id': self.opid})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json(), {'status': 'ok', 'confirmado': False})

    def test_recuperar_cobro_confirmado_sin_duplicar_venta(self):
        pago = self.client.post(self.cobrar, json.dumps(self.payload), content_type='application/json')
        self.assertEqual(pago.status_code, 200, pago.content)
        consulta = self.client.get(self.estado, {'operacion_id': self.opid})
        self.assertEqual(consulta.status_code, 200)
        self.assertTrue(consulta.json()['confirmado'])
        self.assertEqual(consulta.json()['cobro']['total'], 15000.0)
        self.assertEqual(consulta.json()['cobro']['tipo_pago'], 'debito')
        self.assertTrue(consulta.json()['cobro']['reintento'])
        segundo = self.client.post(self.cobrar, json.dumps(self.payload), content_type='application/json')
        self.assertTrue(segundo.json()['reintento'])
        self.assertEqual(Pedido.objects.count(), 1)
        self.assertEqual(OperacionCobroSalon.objects.count(), 1)

    def test_estado_no_autorizado_y_id_invalido(self):
        sin_sesion = Client().get(self.estado, {'operacion_id': self.opid})
        self.assertEqual(sin_sesion.status_code, 403)
        invalido = self.client.get(self.estado, {'operacion_id': '../../../secret'})
        self.assertEqual(invalido.status_code, 400)

    def test_salon_con_servicios_y_herramientas(self):
        respuesta = self.client.get(reverse('pedidos:salon'))
        self.assertEqual(respuesta.status_code, 200)
        html = respuesta.content.decode('utf-8')
        for texto in ('data-charge-status-url=', 'data-charge-url=',
                      'salon-menu-herramientas', 'salon-ver-ventas',
                      'pl-abrir', 'btn-accion-principal',
                      'data-salon-tool-open="mozos"',
                      'data-salon-tool-open="producto"',
                      'data-salon-tool-open="catalogo"'):
            self.assertIn(texto, html)

    def test_panel_conserva_herramientas_rapidas(self):
        respuesta = self.client.get(reverse('pedidos:panel_control'))
        self.assertEqual(respuesta.status_code, 200)
        html = respuesta.content.decode('utf-8')
        for texto in ('sm-herramientas-central', 'sm-herramientas-central__grid',
                      'sm-impresoras-panel', 'btn-tab-menu'):
            self.assertIn(texto, html)
