from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('pedidos', '0028_operacion_cobro_salon')]

    operations = [
        # Solo controla el numero de botones que ve el cajero en la grilla.
        # La operativa existente y las cuentas no se eliminan al bajar el valor.
        migrations.AddField(
            model_name='configuracion',
            name='numero_mesas_visibles',
            field=models.PositiveSmallIntegerField(default=100, verbose_name='Mesas visibles en Salón'),
        ),
    ]
