from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from .models import MarcaNegocio

class MarcaTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_superuser(username='owner-test', email='owner@example.com', password='test-password-strong')
        self.cliente = Client()

    def test_solo_administrador_puede_cambiar_identidad(self):
        resp = self.cliente.get(reverse('marca:configurar'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/mi-negocio/acceso/', resp.url)

    def test_superusuario_guarda_identidad_y_colores(self):
        self.cliente.force_login(self.owner)
        resp = self.cliente.post(reverse('marca:configurar'), {
            'nombre':'Café de prueba', 'nombre_corto':'Café', 'subtitulo':'Comida casera',
            'color_principal':'#102030','color_secundario':'#405060','color_acento':'#708090'
        })
        self.assertEqual(resp.status_code, 302)
        perfil = MarcaNegocio.objects.get(pk=1)
        self.assertEqual(perfil.nombre,'Café de prueba')
        self.assertEqual(perfil.color_acento,'#708090')
        resp_css = self.cliente.get(reverse('marca:tema_css'))
        self.assertTrue(resp_css['Content-Type'].startswith('text/css'))
        self.assertIn(b'#102030', resp_css.content)

    def test_colores_invalidos_se_rechazan(self):
        self.cliente.force_login(self.owner)
        self.cliente.post(reverse('marca:configurar'), {
            'nombre':'Restaurante Test', 'nombre_corto':'Test', 'color_principal':'red; bad',
            'color_secundario':'#405060', 'color_acento':'#708090'
        })
        self.assertNotEqual(MarcaNegocio.objects.get(pk=1).color_principal, 'red; bad')

    def test_manifiesto_publico_contiene_nombre_propio(self):
        MarcaNegocio.objects.create(pk=1,nombre='Restaurante A',nombre_corto='R-A')
        result=self.cliente.get(reverse('marca:manifiesto'))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['name'], 'Restaurante A')

    def test_tema_original_permanece_sin_guardar_colores(self):
        response = self.cliente.get(reverse('marca:tema_css'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'--azul-sanmartin', response.content)

    def test_no_admin_puede_editar_aunque_este_en_panel(self):
        User = get_user_model()
        staff = User.objects.create_user(username='cajero', password='clave-de-prueba')
        self.cliente.force_login(staff)
        respuesta = self.cliente.post(reverse('marca:configurar'), {
            'nombre':'No autorizado', 'nombre_corto':'No',
            'color_principal':'#102030','color_secundario':'#405060','color_acento':'#708090'
        })
        self.assertEqual(respuesta.status_code,302)
        self.assertFalse(MarcaNegocio.objects.exists())

    def test_logo_original_se_conserva_hasta_subir_otro(self):
        respuesta = self.cliente.get(reverse('marca:logo'))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn('/static/img/logo.png', respuesta.url)

    def test_logo_se_guarda_y_lee_sin_archivos_media(self):
        import io
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image
        imagen = Image.new('RGB',(32,32),(250,110,0))
        salida=io.BytesIO()
        imagen.save(salida,format='PNG')
        archivo = SimpleUploadedFile('logo.png',salida.getvalue(),content_type='image/png')
        self.cliente.force_login(self.owner)
        respuesta=self.cliente.post(reverse('marca:configurar'), {
            'nombre':'Prueba Fotos','nombre_corto':'Prueba','subtitulo':'',
            'color_principal':'#FF6600', 'color_secundario':'#FF6600', 'color_acento':'#FF8533',
            'logo':archivo,
        })
        self.assertEqual(respuesta.status_code,302)
        logo=self.cliente.get(reverse('marca:logo'))
        self.assertEqual(logo.status_code,200)
        self.assertEqual(logo['Content-Type'],'image/png')
        self.assertTrue(logo.content.startswith(b'\x89PNG'))
