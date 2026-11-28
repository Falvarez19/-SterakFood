from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('desktop6c', '0001_initial')]

    operations = [
        migrations.CreateModel(
            name='DesktopPairingCode',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('installation_id', models.UUIDField(db_index=True)),
                ('code_hash', models.CharField(max_length=64, unique=True)),
                ('label', models.CharField(max_length=80)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('redeemed_at', models.DateTimeField(null=True, blank=True)),
                ('device_uid', models.UUIDField(null=True, blank=True)),
                ('token', models.ForeignKey(to='desktop6c.desktopaccesstoken', null=True,
                                            blank=True, on_delete=django.db.models.deletion.PROTECT)),
            ],
        ),
        migrations.CreateModel(
            name='DesktopRegisteredDevice',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('device_uid', models.UUIDField(unique=True)),
                ('installation_id', models.UUIDField(db_index=True)),
                ('label', models.CharField(max_length=80)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('revoked_at', models.DateTimeField(null=True, blank=True)),
                ('token', models.OneToOneField(to='desktop6c.desktopaccesstoken',
                                                on_delete=django.db.models.deletion.PROTECT)),
            ],
        ),
    ]
