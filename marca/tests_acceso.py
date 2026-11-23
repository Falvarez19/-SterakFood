"""Comprobaciones de acceso a identidad por instalación SterakFood."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AccesoPropietarioTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.duenio = User.objects.create_superuser(
            username='duenio-test', email='duenio@example.invalid', password='ClaveTemporalSegura123!'
        )
        self.cajero = User.objects.create_user(
            username='cajero-test', password='ClaveTemporalSegura123!'
        )

    def test_no_redirige_a_admin_login(self):
        respuesta = self.client.get(reverse('marca:configurar'))
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.url, reverse('marca:acceso'))
        acceso = self.client.get(respuesta.url)
        self.assertContains(acceso, 'Acceso de propietario')

    def test_superusuario_ingresa_sin_django_admin(self):
        respuesta = self.client.post(reverse('marca:acceso'), {
            'username': 'duenio-test', 'password': 'ClaveTemporalSegura123!'
        })
        self.assertRedirects(respuesta, reverse('marca:configurar'), fetch_redirect_response=True)
        self.assertTrue(self.client.session['_auth_user_id'])

    def test_cajero_no_accede_a_personalizacion(self):
        respuesta = self.client.post(reverse('marca:acceso'), {
            'username': 'cajero-test', 'password': 'ClaveTemporalSegura123!'
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'no tiene permiso')
        respuesta_marca = self.client.get(reverse('marca:configurar'))
        self.assertRedirects(respuesta_marca, reverse('marca:acceso'), fetch_redirect_response=False)
