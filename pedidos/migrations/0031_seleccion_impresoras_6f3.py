"""Opciones de ruta por sector; compatibles con la configuración anterior."""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('pedidos', '0030_facturacion_integral_5j')]

    operations = [
        migrations.AddField(model_name='configuracionimpresoraspos', name='caja_modo',
                            field=models.CharField(max_length=10, default='windows')),
        migrations.AddField(model_name='configuracionimpresoraspos', name='caja_ip',
                            field=models.GenericIPAddressField(protocol='IPv4', blank=True, null=True, default=None)),
        migrations.AddField(model_name='configuracionimpresoraspos', name='cocina_modo',
                            field=models.CharField(max_length=10, default='tcp')),
        migrations.AddField(model_name='configuracionimpresoraspos', name='cocina_windows',
                            field=models.CharField(max_length=120, blank=True, default='')),
        migrations.AddField(model_name='configuracionimpresoraspos', name='barra_modo',
                            field=models.CharField(max_length=10, default='tcp')),
        migrations.AddField(model_name='configuracionimpresoraspos', name='barra_windows',
                            field=models.CharField(max_length=120, blank=True, default='')),
    ]
