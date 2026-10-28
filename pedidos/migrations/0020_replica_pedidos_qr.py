from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('pedidos', '0019_respaldo_mesas_local')]

    operations = [
        migrations.CreateModel(name='PedidoQRRemoto', fields=[
            ('id', models.BigAutoField(primary_key=True, serialize=False)),
            ('origen_id', models.PositiveBigIntegerField(unique=True)),
            ('estado', models.CharField(max_length=20, blank=True)),
            ('cliente', models.CharField(max_length=100, blank=True)),
            ('telefono', models.CharField(max_length=20, blank=True)),
            ('tipo_pago', models.CharField(max_length=50, blank=True)),
            ('entrega', models.CharField(max_length=50, blank=True)),
            ('mesa', models.CharField(max_length=10, blank=True)),
            ('mostrador', models.CharField(max_length=80, blank=True)),
            ('total', models.DecimalField(decimal_places=2, max_digits=10, default=0)),
            ('fecha_remota', models.DateTimeField()),
            ('productos', models.JSONField(default=list)),
            ('ultima_consulta', models.DateTimeField(auto_now=True)),
        ], options={'ordering': ['-fecha_remota','-origen_id']}),
        migrations.CreateModel(name='EstadoSyncQR', fields=[
            ('id', models.BigAutoField(primary_key=True, serialize=False)),
            ('ultima_conexion', models.DateTimeField(blank=True, null=True)),
            ('ultimo_error', models.CharField(max_length=250, blank=True)),
            ('ultima_cantidad', models.PositiveIntegerField(default=0)),
        ])
    ]
