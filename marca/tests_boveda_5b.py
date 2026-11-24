"""Pruebas de seguridad 5B. No realizan llamadas a ARCA ni generan CAE."""
from unittest.mock import patch

from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .arca_vault_5a import ConfiguracionSeguraError, runtime_emision


@override_settings(SM_LOCAL_MODE=False)
class Boveda5BSeguridadTests(TestCase):
    def setUp(self):
        self.url = reverse('marca:arca_comprobar_boveda_5b')
        User = get_user_model()
        self.propietario = User.objects.create_superuser(username='propietario-5b', email='p5b@example.invalid', password='PruebaSegura123!')
        self.cajero = User.objects.create_user(username='cajero-5b', password='PruebaSegura123!')

    def test_anonimo_no_puede_probar_la_boveda(self):
        self.assertEqual(self.client.post(self.url).status_code, 403)

    def test_cajero_no_puede_probar_la_boveda(self):
        self.client.force_login(self.cajero)
        self.assertEqual(self.client.post(self.url).status_code, 403)

    def test_propietario_prueba_cifrado_sin_credenciales(self):
        self.client.force_login(self.propietario)
        clave = Fernet.generate_key().decode('ascii')
        with patch.dict('os.environ', {'STERAK_ARCA_VAULT_KEY': clave}):
            response = self.client.post(self.url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bóveda lista')

    def test_sin_clave_no_pasa_el_control(self):
        self.client.force_login(self.propietario)
        with patch.dict('os.environ', {'STERAK_ARCA_VAULT_KEY': ''}):
            response = self.client.post(self.url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bóveda no disponible')

    def test_sin_activar_bloquea_emision_legada(self):
        with patch.dict('os.environ', {'ARCA_FISCAL_ENABLED': '1'}):
            with self.assertRaises(ConfiguracionSeguraError):
                runtime_emision()
