import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(name='Desktop6eDevice',fields=[
            ('id',models.BigAutoField(primary_key=True,serialize=False)),
            ('uid',models.UUIDField(default=uuid.uuid4,editable=False,unique=True)),
            ('created_at',models.DateTimeField(auto_now_add=True)),
        ]),
        migrations.CreateModel(name='Desktop6eSettings',fields=[
            ('id',models.BigAutoField(primary_key=True,serialize=False)),
            ('created_at',models.DateTimeField(auto_now_add=True)),
            ('enviar_automaticamente',models.BooleanField(default=False)),
            ('updated_at',models.DateTimeField(auto_now=True)),
        ]),
        migrations.CreateModel(name='Desktop6eOutbox',fields=[
            ('event_id',models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),
            ('tipo',models.CharField(max_length=32)),('origen',models.CharField(max_length=110)),
            ('payload',models.JSONField()),('digest',models.CharField(max_length=64)),
            ('status',models.CharField(db_index=True,default='pendiente',max_length=12)),
            ('intentos',models.PositiveIntegerField(default=0)),
            ('error',models.CharField(blank=True,default='',max_length=240)),
            ('created_at',models.DateTimeField(auto_now_add=True)),
            ('acknowledged_at',models.DateTimeField(blank=True,null=True)),
        ], options={'ordering':['created_at','event_id']}),
        migrations.CreateModel(name='Desktop6eInbox',fields=[
            ('event_id',models.UUIDField(editable=False,primary_key=True,serialize=False)),
            ('device_id',models.UUIDField()),('installation_id',models.UUIDField()),
            ('tipo',models.CharField(max_length=32)),('origen',models.CharField(max_length=110)),
            ('payload',models.JSONField()),('digest',models.CharField(max_length=64)),
            ('token_label',models.CharField(blank=True,max_length=80)),
            ('received_at',models.DateTimeField(auto_now_add=True)),
        ], options={'ordering':['-received_at']}),
        migrations.AddConstraint(model_name='desktop6eoutbox',constraint=models.UniqueConstraint(fields=('tipo','origen'),name='sf6e_outbox_origen_unico')),
        migrations.AddConstraint(model_name='desktop6einbox',constraint=models.UniqueConstraint(fields=('device_id','tipo','origen'),name='sf6e_inbox_origen_unico')),
    ]
