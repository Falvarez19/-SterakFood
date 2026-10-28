"""Pruebas del módulo para llevar: cola de cocina, cobro e idempotencia."""
import json
import uuid
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from .models import Categoria, DetallePedido, Pedido, PedidoParaLlevar, Producto, Configuracion


class ParaLlevarTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('pedidos:pedidos_para_llevar')
        cat_cocina = Categoria.objects.create(nombre='Comidas')
        cat_barra = Categoria.objects.create(nombre='Bebidas')
        self.pasta = Producto.objects.create(nombre='Fideos', categoria=cat_cocina, precio=Decimal('10000.00'))
        self.agua = Producto.objects.create(nombre='Agua', categoria=cat_barra, precio=Decimal('2500.00'))
        Configuracion.objects.create(pk=1, salon_habilitado=True)
        self.client.session['dashboard_auth'] = True
        session = self.client.session
        session['dashboard_auth'] = True
        session.save()
        self.uuid = str(uuid.uuid4())

    def post(self, url, data):
        return self.client.post(url, data=json.dumps(data), content_type='application/json')

    def pedido_data(self, **extra):
        data = {'solicitud_id': self.uuid, 'cliente': 'Lu', 'notas': 'Sin cebolla',
                'pago': 'pendiente', 'items': [
                    {'producto_id': self.pasta.id, 'cantidad': 2, 'precio': '0.01'},
                    {'producto_id': self.agua.id, 'cantidad': 1}]}
        data.update(extra)
        return data

    def test_exige_login(self):
        anon = Client()
        self.assertEqual(anon.get(self.url).status_code, 403)
        self.assertEqual(anon.post(self.url, '{}', content_type='application/json').status_code, 403)

    def test_crear_imprime_cocina_incluso_bebidas_y_no_registra_venta_pendiente(self):
        response = self.post(self.url, self.pedido_data())
        self.assertEqual(response.status_code, 201, response.content)
        pedido = Pedido.objects.get(pk=response.json()['pedido_id'])
        self.assertEqual(pedido.tipo_entrega, 'para_llevar')
        self.assertEqual(pedido.total, Decimal('22500.00'))
        self.assertEqual(pedido.tipo_pago, 'pendiente_para_llevar')
        self.assertIsNone(pedido.numero_mesa)
        self.assertEqual(pedido.para_llevar.observaciones, 'Sin cebolla')
        self.assertEqual(DetallePedido.objects.filter(pedido=pedido).count(), 2)
        cola = self.client.get(reverse('pedidos:api_pedidos_pendientes')).json()['pedidos']
        ticket = next(p for p in cola if p['id'] == pedido.id)
        self.assertEqual(ticket['entrega'], 'PARA_LLEVAR')
        self.assertEqual(len(ticket['items_cocina']), 2)
        self.assertEqual(ticket['items_barra'], [])
        self.assertFalse(ticket['imprimir_ticket_cobro'])
        self.assertEqual(ticket['notas'], 'Sin cebolla')
        self.assertEqual(ticket['pago'], 'NO PAGADO')
        resumen = self.client.get(reverse('pedidos:api_resumen_ventas')).json()
        self.assertEqual(resumen['gran_total'], 0.0)

    def test_uuid_evitar_duplicados(self):
        a = self.post(self.url, self.pedido_data())
        b = self.post(self.url, self.pedido_data())
        self.assertEqual(a.status_code, 201)
        self.assertEqual(b.status_code, 200)
        self.assertTrue(b.json()['duplicado'])
        self.assertEqual(Pedido.objects.count(), 1)
        self.assertEqual(PedidoParaLlevar.objects.count(), 1)

    def test_cobrar_no_reimprime_ni_factura(self):
        pedido_id = self.post(self.url, self.pedido_data()) .json()['pedido_id']
        self.client.post(reverse('pedidos:api_marcar_impreso', args=[pedido_id]))
        r = self.post(reverse('pedidos:cobrar_para_llevar',args=[pedido_id]), {'pago':'debito'})
        self.assertEqual(r.status_code, 200, r.content)
        pedido=Pedido.objects.get(pk=pedido_id)
        self.assertEqual(pedido.tipo_pago,'debito')
        self.assertTrue(pedido.impreso_caja)
        self.assertEqual(self.post(reverse('pedidos:cobrar_para_llevar',args=[pedido_id]), {'pago':'debito'}).status_code,409)
        self.assertEqual(self.client.get(reverse('pedidos:api_resumen_ventas')).json()['gran_total'],22500.0)
        self.assertEqual(self.client.get(reverse('pedidos:salon_resumen_ventas_api')).json()['total_registrado'],22500.0)
        self.assertEqual(self.post(reverse('pedidos:estado_para_llevar',args=[pedido_id]), {'estado':'entregado'}).status_code,200)

    def test_no_se_puede_entregar_sin_cobrar(self):
        pedido_id=self.post(self.url,self.pedido_data()).json()['pedido_id']
        self.assertEqual(self.post(reverse('pedidos:estado_para_llevar',args=[pedido_id]), {'estado':'entregado'}).status_code,409)

    def test_validar_catalogo_y_medios_pago(self):
        self.assertEqual(self.post(self.url,self.pedido_data(items=[{'producto_id':self.pasta.id,'cantidad':-1}])).status_code,400)
        self.assertEqual(self.post(self.url,self.pedido_data(pago='tarjeta')).status_code,400)
        self.pasta.disponible=False;self.pasta.save()
        self.assertEqual(self.post(self.url,self.pedido_data()).status_code,409)

    def test_boton_y_modal_en_salon(self):
        response=self.client.get(reverse('pedidos:salon'))
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'🥡 Para llevar')
        self.assertContains(response,'pl-dialog')
        self.assertContains(response,'id="pl-celiaco-pedido"')
        self.assertContains(response,'CELÍACO (pedido completo)')
        self.assertContains(response,'CELÍACO (solo este plato)')

    def test_venta_separada_en_cierre(self):
        self.post(self.url, self.pedido_data(pago='efectivo'))
        cierre = self.client.get(reverse('pedidos:api_resumen_ventas')).json()
        self.assertEqual(cierre['gran_total'],22500.0)
        self.assertEqual(next(x['nombre'] for x in cierre['mostradores'] if x['cantidad_pedidos'] == 1), 'Para llevar')

class ParaLlevarMenuCompartidoTests(TestCase):
    """Producto, variantes, adicionales, precios e impresión son los del menú público."""
    def setUp(self):
        from .models import PuntoVenta
        self.client = Client()
        session = self.client.session
        session['dashboard_auth'] = True
        session.save()
        Configuracion.objects.create(pk=1, salon_habilitado=True)
        self.puesto = PuntoVenta.objects.create(nombre='Buffet', slug='buffet', telefono='')
        self.categoria = Categoria.objects.create(nombre='Comidas')
        self.milanesa = Producto.objects.create(
            nombre='Milanesa', precio=Decimal('10000.00'), categoria=self.categoria,
            variantes='Común, Napolitana (+2500)', guarniciones='Papas, Ensalada',
            adicionales='Huevo (+500), Sin sal',
        )
        self.milanesa.puntos_venta.add(self.puesto)
        self.solo_salon = Producto.objects.create(
            nombre='Servicio de mesa', precio=Decimal('900'),
            categoria=Categoria.objects.create(nombre='Salon'),
        )
        self.solo_salon.puntos_venta.add(self.puesto)
        self.url = reverse('pedidos:pedidos_para_llevar')

    def guardar(self, items):
        return self.client.post(self.url, json.dumps({
            'solicitud_id': str(uuid.uuid4()), 'pago': 'pendiente', 'items': items,
        }), content_type='application/json')

    def test_catalogo_muestra_exactamente_las_opciones_del_menu_publico(self):
        datos = self.client.get(self.url).json()['catalogo']
        self.assertEqual(len(datos), 1)
        self.assertEqual(datos[0]['nombre'], 'Milanesa')
        self.assertEqual(datos[0]['opciones']['variante'], ['Común', 'Napolitana (+2500)'])
        self.assertEqual(datos[0]['opciones']['guarnicion'], ['Papas', 'Ensalada'])
        self.assertNotIn(self.solo_salon.id, [p['id'] for p in datos])

    def test_milanesa_napo_y_comun_son_items_separados_con_sus_precios(self):
        r = self.guardar([
            {'producto_id': self.milanesa.id, 'cantidad': 2, 'opciones': {
                'variante': 'Napolitana (+2500)', 'guarnicion': 'Papas',
                'adicional': ['Huevo (+500)']}},
            {'producto_id': self.milanesa.id, 'cantidad': 1, 'opciones': {
                'variante': 'Común', 'guarnicion': 'Ensalada', 'adicional': []}},
        ])
        self.assertEqual(r.status_code, 201, r.content)
        pedido = Pedido.objects.get(pk=r.json()['pedido_id'])
        self.assertEqual(pedido.total, Decimal('36000.00'))
        detalles = list(pedido.items.order_by('-precio_unitario'))
        self.assertEqual(len(detalles), 2)
        self.assertEqual(detalles[0].variante_elegida, 'Napolitana (+2500)')
        self.assertEqual(detalles[0].guarnicion_elegida, 'Papas')
        self.assertEqual(detalles[0].adicional_elegido, 'Huevo (+500)')
        self.assertEqual(detalles[0].precio_unitario, Decimal('13000.00'))
        self.assertEqual(detalles[1].precio_unitario, Decimal('10000.00'))
        cola = self.client.get(reverse('pedidos:api_pedidos_pendientes')).json()['pedidos']
        impresion = next(p for p in cola if p['id'] == pedido.id)
        texto = '\n'.join(i['nombre'] for i in impresion['items_cocina'])
        self.assertIn('Napolitana', texto)
        self.assertNotIn('(+2500)', texto)
        self.assertNotIn('(+500)', texto)
        self.assertIn('Papas', texto)
        self.assertIn('Extra: Huevo', texto)
        self.assertIn('Común', texto)
        self.assertEqual(impresion['items_barra'], [])

    def test_rechaza_opcion_falsa_o_sin_elegir_variante(self):
        for opciones in ({'variante':'Premium (+9999)','guarnicion':'Papas'},
                         {'guarnicion':'Papas'},
                         {'variante':'Común','guarnicion':'Papas','adicional':['Inventado']}):
            r = self.guardar([{'producto_id':self.milanesa.id,'cantidad':1,'opciones':opciones}])
            self.assertEqual(r.status_code,400,r.content)
        self.assertEqual(Pedido.objects.count(),0)

    def test_producto_fuera_de_menu_no_se_puede_pedir(self):
        r = self.guardar([{'producto_id':self.solo_salon.id,'cantidad':1}])
        self.assertEqual(r.status_code,409)
        self.assertEqual(Pedido.objects.count(),0)

    def test_adicionales_dobles_y_descuentos_no_se_confunden(self):
        self.milanesa.adicionales='Huevo (+500), Sin sal, Sin guarnición (-1000)'
        self.milanesa.save(update_fields=['adicionales'])
        r=self.guardar([{'producto_id':self.milanesa.id,'cantidad':1,'opciones':{
            'variante':'Común', 'guarnicion':'Papas',
            'adicional':['Huevo (+500)','Sin guarnición (-1000)']}}])
        self.assertEqual(r.status_code,201,r.content)
        pedido=Pedido.objects.get(pk=r.json()['pedido_id'])
        self.assertEqual(pedido.total,Decimal('9500.00'))
        self.assertIn('Huevo (+500)',pedido.items.get().adicional_elegido)
        self.assertIn('Sin guarnición (-1000)',pedido.items.get().adicional_elegido)

    def test_tirita_cocina_recibe_opciones_y_puntos_sin_importes(self):
        r=self.guardar([{'producto_id':self.milanesa.id,'cantidad':1,'opciones':{
            'variante':'Napolitana (+2500)', 'guarnicion':'Papas', 'adicional':['Huevo (+500)']}}])
        self.assertEqual(r.status_code,201)
        data=self.client.get(reverse('pedidos:api_pedidos_pendientes')).json()
        comanda=next(p for p in data['pedidos'] if p['id']==r.json()['pedido_id'])
        item=comanda['items_cocina'][0]
        self.assertEqual(item['plato'],'Milanesa')
        self.assertIn('Napolitana',item['opciones'])
        self.assertIn('Extra: Huevo',item['opciones'])
        self.assertNotIn('(+2500)',str(item))
        self.assertNotIn('(+500)',str(item))

    def test_aviso_celiaco_por_plato_sin_cambiar_precios_ni_puntos(self):
        self.milanesa.puntos_coccion = 'Jugoso, A punto, Bien cocido'
        self.milanesa.save(update_fields=['puntos_coccion'])
        opciones = {'variante': 'Napolitana (+2500)', 'guarnicion': 'Papas',
                    'punto': 'Bien cocido', 'adicional': ['Huevo (+500)']}
        r = self.guardar([
            {'producto_id': self.milanesa.id, 'cantidad': 1, 'opciones': opciones,
             'aviso_celiaco': True},
            {'producto_id': self.milanesa.id, 'cantidad': 1, 'opciones': opciones,
             'aviso_celiaco': False},
        ])
        self.assertEqual(r.status_code, 201, r.content)
        pedido = Pedido.objects.get(pk=r.json()['pedido_id'])
        self.assertEqual(pedido.total, Decimal('26000.00'))
        self.assertEqual(pedido.items.count(), 2)
        self.assertEqual(sorted(d.aviso_celiaco for d in pedido.items.all()), [False, True])
        cola = self.client.get(reverse('pedidos:api_pedidos_pendientes')).json()['pedidos']
        comanda = next(p for p in cola if p['id'] == pedido.id)
        self.assertTrue(comanda['alerta_celiaco'])
        self.assertEqual(sum(bool(i['aviso_celiaco']) for i in comanda['items_cocina']), 1)
        for item in comanda['items_cocina']:
            self.assertIn('Punto: Bien cocido', item['opciones'])
            self.assertIn('Napolitana', item['opciones'])
            self.assertIn('Extra: Huevo', item['opciones'])
            self.assertNotIn('(+2500)', str(item))
            self.assertNotIn('(+500)', str(item))
            self.assertNotIn('13000', str(item))
            self.assertNotIn('subtotal', item)
        self.assertEqual(comanda['items_barra'], [])
        # Los precios siguen guardados y se conservan para caja/ventas.
        self.assertEqual([d.precio_unitario for d in pedido.items.all()],
                         [Decimal('13000.00'), Decimal('13000.00')])
        self.assertIn('$', str(comanda['items_caja']))
        historial = self.client.get(self.url).json()['pedidos']
        self.assertTrue(next(p for p in historial if p['id'] == pedido.id)['aviso_celiaco'])

    def test_aviso_celiaco_rechaza_valores_no_booleanos(self):
        r = self.guardar([{'producto_id': self.milanesa.id, 'cantidad': 1,
                          'opciones': {'variante': 'Común', 'guarnicion': 'Papas'},
                          'aviso_celiaco': 'no'}])
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Pedido.objects.count(), 0)
