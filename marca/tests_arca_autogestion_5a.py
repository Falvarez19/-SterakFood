"""Pruebas locales de la bóveda 5A. No contactan ARCA ni generan CAE."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from cryptography import x509
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from django.test import SimpleTestCase

from marca.arca_vault_5a import (
    MAX_P12_BYTES, ConfiguracionSeguraError, abrir_p12,
    cifrar_archivo, _descifrar,
)


class BovedaFiscalTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        nombre = x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, 'Certificado ficticio de prueba')])
        hoy = datetime.now(timezone.utc)
        certificado = (x509.CertificateBuilder().subject_name(nombre).issuer_name(nombre)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(hoy-timedelta(days=1))
            .not_valid_after(hoy+timedelta(days=90)).sign(key, hashes.SHA256()))
        cls.p12 = pkcs12.serialize_key_and_certificates(
            b'prueba', key, certificado, None,
            serialization.BestAvailableEncryption(b'clave-de-prueba'))

    def test_p12_se_abre_solo_con_password_correcto(self):
        clave, cert, expiracion, huella = abrir_p12(self.p12, 'clave-de-prueba')
        self.assertIsNotNone(clave)
        self.assertIsNotNone(cert)
        self.assertGreater(expiracion, datetime.now(timezone.utc))
        self.assertEqual(len(huella), 64)
        with self.assertRaises(ConfiguracionSeguraError):
            abrir_p12(self.p12, 'password-equivocado')

    def test_cifrado_no_contiene_certificado_ni_password_y_exige_clave_estable(self):
        clave = Fernet.generate_key().decode('ascii')
        with patch.dict('os.environ', {'STERAK_ARCA_VAULT_KEY': clave}):
            encrypted = cifrar_archivo(self.p12, 'clave-de-prueba')
            self.assertNotIn(self.p12, encrypted)
            self.assertNotIn(b'clave-de-prueba', encrypted)
            plain, pwd = _descifrar(type('CredencialFalsa', (), {'secreto_cifrado': encrypted})())
            self.assertEqual(plain, self.p12)
            self.assertEqual(pwd, 'clave-de-prueba')
        with patch.dict('os.environ', {'STERAK_ARCA_VAULT_KEY': Fernet.generate_key().decode('ascii')}):
            with self.assertRaises(ConfiguracionSeguraError):
                _descifrar(type('CredencialFalsa', (), {'secreto_cifrado': encrypted})())

    def test_archivo_grande_rechazado_antes_de_cifrar(self):
        with self.assertRaises(ConfiguracionSeguraError):
            cifrar_archivo(b'a' * (MAX_P12_BYTES + 1), 'clave')
