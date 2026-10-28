import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from .models import Categoria, Producto, Pedido, DetallePedido, Configuracion, CuentaCorriente, MovimientoCuentaCorriente

class CierreSalonTests(TestCase):
    def setUp(self):
        self.client=Client()
        s=self.client.session
        s['dashboard_auth']=True
        s.save()
        Configuracion.objects.create(pk=1, salon_habilitado=True)
        cat=Categoria.objects.create(nombre='Salon')
        self.p1=Producto.objects.create(categoria=cat,nombre='7UP',codigo_rapido='157',precio=Decimal('3500'))
        self.p2=Producto.objects.create(categoria=cat,nombre='BATATAS FRITAS',codigo_rapido='200',precio=Decimal('11000'))
        self.p3=Producto.objects.create(categoria=cat,nombre='ALFAJOR',codigo_rapido='228',precio=Decimal('2500'))
        self.url=reverse('pedidos:cobrar_mesa_salon')
    def request(self,medio='debito',**kwargs):
        d={'mesa':'1','tipo_pago':medio,'mozo':'Gaby','modo_fiscal':False,'items':[
            {'producto_id':self.p1.id,'codigo':'157','nombre':'7UP','precio':3500,'cantidad':3},
            {'producto_id':self.p2.id,'codigo':'200','nombre':'BATATAS FRITAS','precio':11000,'cantidad':1},
            {'producto_id':self.p3.id,'codigo':'228','nombre':'ALFAJOR','precio':2500,'cantidad':1},
        ]}
        d.update(kwargs)
        return self.client.post(self.url,json.dumps(d),content_type='application/json')
    def test_all_methods_close(self):
        for medio in ['efectivo','debito','mercadopago']:
            with self.subTest(medio=medio):
                r=self.request(medio)
                self.assertEqual(r.status_code,200,r.content)
                self.assertEqual(r.json()['status'],'ok')
                self.assertEqual(r.json()['total'],24000.0)
                self.assertEqual(Pedido.objects.last().tipo_pago,medio)
                self.assertEqual(Pedido.objects.last().total,24000)
    def test_missing_product_does_not_close(self):
        r=self.request(items=[{'codigo':'99999','precio':100,'cantidad':1}])
        self.assertEqual(r.status_code,400, r.content)
        self.assertEqual(Pedido.objects.count(),0)
    def test_unauthenticated_no_close(self):
        client=Client()
        r=client.post(self.url,json.dumps({'mesa':'1'}),content_type='application/json')
        self.assertEqual(r.status_code,403)
    def test_reintento_no_duplica_efectivo(self):
        a=self.request('efectivo',operacion_id='abc-efectivo-0000001')
        b=self.request('efectivo',operacion_id='abc-efectivo-0000001')
        self.assertEqual(a.status_code,200,a.content)
        self.assertEqual(b.status_code,200,b.content)
        self.assertTrue(b.json()['reintento'])
        self.assertEqual(Pedido.objects.count(),1)
        self.assertEqual(DetallePedido.objects.count(),3)
    def test_reintento_no_duplica_debito(self):
        a=self.request('debito',operacion_id='abc-debito-00000002')
        b=self.request('debito',operacion_id='abc-debito-00000002')
        self.assertEqual(a.status_code,200,a.content)
        self.assertEqual(b.status_code,200,b.content)
        self.assertEqual(Pedido.objects.count(),1)
    def test_reutilizar_id_con_items_distintos_no_cobra(self):
        a=self.request('mercadopago',operacion_id='abc-mercado-000001')
        b=self.request('mercadopago',operacion_id='abc-mercado-000001',items=[{
            'producto_id':self.p1.id,'codigo':'157','precio':3500,'cantidad':1,
        }])
        self.assertEqual(a.status_code,200)
        self.assertEqual(b.status_code,400,b.content)
        self.assertEqual(Pedido.objects.count(),1)
    def test_id_antiguo_usa_codigo_actual(self):
        a=self.request('debito',operacion_id='abc-codigo-000001',items=[{
            'producto_id':99999,'codigo':'157','nombre':'7UP','precio':3500,'cantidad':3,
        }])
        self.assertEqual(a.status_code,200,a.content)
        self.assertEqual(DetallePedido.objects.get().producto_id,self.p1.id)
    def test_producto_inexistente_error_claro(self):
        a=self.request('debito',operacion_id='abc-invalido-00001',items=[{
            'producto_id':9999,'codigo':'9998','nombre':'Viejo','precio':400,'cantidad':1,
        }])
        self.assertEqual(a.status_code,400,a.content)
        self.assertIn('Viejo',a.json()['mensaje'])
        self.assertEqual(Pedido.objects.count(),0)
    def test_cuenta_corriente_registra_deuda_solo_una_vez(self):
        cuenta=CuentaCorriente.objects.create(nombre='Cliente prueba',activa=True)
        a=self.request('cuenta_corriente',operacion_id='abc-fiado-00000001',cuenta_corriente_id=cuenta.pk)
        b=self.request('cuenta_corriente',operacion_id='abc-fiado-00000001',cuenta_corriente_id=cuenta.pk)
        self.assertEqual(a.status_code,200,a.content)
        self.assertEqual(b.status_code,200,b.content)
        self.assertEqual(MovimientoCuentaCorriente.objects.count(),1)
        self.assertEqual(MovimientoCuentaCorriente.objects.first().monto,Decimal('-24000'))
        self.assertEqual(Pedido.objects.count(),1)
    def test_cobro_parcial_mantiene_la_parte_no_cobrada(self):
        a=self.request('efectivo',operacion_id='abc-parcial-000001',items=[{
            'producto_id': self.p1.id,'codigo':'157','precio':3500,'cantidad':1,
        }])
        self.assertEqual(a.status_code,200,a.content)
        self.assertEqual(a.json()['total'],3500.0)
        self.assertEqual(Pedido.objects.count(),1)
    def test_fiscal_no_se_activa_al_elegir_debito(self):
        from .models import BorradorFiscal, FacturaFiscal
        a=self.request('debito',operacion_id='abc-no-fiscal-0001')
        self.assertEqual(a.status_code,200,a.content)
        self.assertEqual(BorradorFiscal.objects.count(),0)
        self.assertEqual(FacturaFiscal.objects.count(),0)
