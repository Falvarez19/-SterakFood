from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('desktop6e', '0001_initial')]

    operations = [
        migrations.CreateModel(
            name='Desktop6f12MesaMirror',
            fields=[
                ('device_id', models.UUIDField(primary_key=True, editable=False, serialize=False)),
                ('installation_id', models.UUIDField()),
                ('version', models.PositiveBigIntegerField(default=0)),
                ('snapshot', models.JSONField(default=dict)),
                ('digest', models.CharField(max_length=64)),
                ('token_label', models.CharField(max_length=80, blank=True, default='')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'Replica de mesas Desktop (solo lectura)'},
        ),
    ]
