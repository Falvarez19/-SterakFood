import uuid
from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [('pedidos', '0023_configuracion_impresoras_pos')]
    operations = [migrations.CreateModel(
        name='EventoSyncPOS', fields=[
            ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, serialize=False, editable=False)),
            ('tipo', models.CharField(max_length=16)),
            ('payload', models.JSONField(default=dict)),
            ('creado', models.DateTimeField(auto_now_add=True)),
            ('enviado', models.BooleanField(default=False)),
            ('enviado_en', models.DateTimeField(null=True, blank=True)),
            ('error', models.CharField(max_length=240, blank=True, default='')),
        ], options={'ordering':['creado','id'],'verbose_name':'Evento POS para sincronizar'}
    )]
