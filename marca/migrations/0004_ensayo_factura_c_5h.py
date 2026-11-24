# Generado por el instalador SterakFood 5H. No aplicar en producción antes de respaldar PostgreSQL.
import uuid
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('marca', '0003_visual_menu_6a')]
    operations = [
        migrations.CreateModel(
            name='ArcaEnsayoFacturaC',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('operacion_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('entorno', models.CharField(default='homologacion', editable=False, max_length=15)),
                ('cuit_emisor', models.CharField(max_length=11)),
                ('punto_venta', models.PositiveIntegerField()),
                ('numero', models.PositiveIntegerField()),
                ('total', models.DecimalField(decimal_places=2, max_digits=9)),
                ('fecha_comprobante', models.CharField(max_length=8)),
                ('estado', models.CharField(choices=[('incierto','Verificar en ARCA antes de reintentar'), ('autorizada','CAE homologación recibido'), ('rechazada','Rechazada: requiere revisión')], default='incierto', max_length=15)),
                ('cae', models.CharField(blank=True, default='', max_length=20)),
                ('vence_cae', models.CharField(blank=True, default='', max_length=8)),
                ('url_qr', models.TextField(blank=True, default='')),
                ('detalle_publico', models.CharField(blank=True, default='', max_length=240)),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('actualizado', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name':'Ensayo de Factura C (SIN valor fiscal)',
                'verbose_name_plural':'Ensayos de Factura C (SIN valor fiscal)',
            },
        ),
        migrations.AddConstraint(
            model_name='arcaensayofacturac',
            constraint=models.UniqueConstraint(fields=('entorno','cuit_emisor','punto_venta','numero'), name='sterak_5h_numero_c_unico'),
        ),
    ]
