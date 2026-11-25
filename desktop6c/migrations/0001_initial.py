import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(name='WebInstallation', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('instance_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
        ]),
        migrations.CreateModel(name='DesktopAccessToken', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('label', models.CharField(max_length=80)),
            ('token_hash', models.CharField(max_length=64, unique=True)),
            ('active', models.BooleanField(default=True)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('last_used_at', models.DateTimeField(blank=True, null=True)),
        ]),
        migrations.CreateModel(name='DesktopLink', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('server_url', models.URLField(max_length=300)),
            ('web_instance_id', models.UUIDField()),
            ('token_ciphertext', models.TextField()),
            ('last_sync_at', models.DateTimeField(blank=True, null=True)),
            ('last_error', models.CharField(blank=True, default='', max_length=500)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
        ]),
        migrations.CreateModel(name='RemoteObjectMap', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('kind', models.CharField(choices=[('producto', 'Producto'), ('categoria', 'Categoría'), ('puesto', 'Punto de venta')], max_length=16)),
            ('remote_id', models.PositiveIntegerField()),
            ('local_id', models.PositiveIntegerField()),
            ('photo_source', models.CharField(blank=True, default='', max_length=500)),
        ]),
        migrations.CreateModel(name='DesktopSyncEvent', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('ok', models.BooleanField()),
            ('summary', models.CharField(max_length=350)),
            ('products_count', models.PositiveIntegerField(default=0)),
        ], options={'ordering': ['-created_at']}),
        migrations.AddConstraint(model_name='remoteobjectmap', constraint=models.UniqueConstraint(fields=('kind', 'remote_id'), name='desktop6c_remote_unique')),
    ]
