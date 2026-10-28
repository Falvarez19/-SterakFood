from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('pedidos', '0022_reinicio_historial_ventas_seguro')]
    operations = [
        migrations.CreateModel(
            name='ConfiguracionImpresorasPOS',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(default='Terminal principal', max_length=80)),
                ('caja_windows', models.CharField(default='FACTURA_PYTHON', max_length=120)),
                ('ip_cocina', models.GenericIPAddressField(default='192.168.1.100', protocol='IPv4')),
                ('ip_barra', models.GenericIPAddressField(default='192.168.1.101', protocol='IPv4')),
                ('ancho_ticket', models.PositiveSmallIntegerField(default=32)),
                ('token_hash', models.CharField(blank=True, default='', max_length=64)),
                ('actualizado', models.DateTimeField(auto_now=True)),
                ('ultima_conexion', models.DateTimeField(blank=True, null=True)),
            ],
            options={'verbose_name':'Configuración impresora POS', 'verbose_name_plural':'Configuración impresoras POS'},
        ),
    ]
