# SterakFood v104 - Evitar duplicaciones al cargar al fiado desde Salón POS.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('pedidos', '0015_cuentas_corrientes'),
    ]

    operations = [
        migrations.AddField(
            model_name='movimientocuentacorriente',
            name='operacion_id',
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),
    ]
