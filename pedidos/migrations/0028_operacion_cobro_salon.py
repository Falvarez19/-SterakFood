from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('pedidos', '0027_detallepedido_aviso_celiaco')]

    operations = [
        migrations.CreateModel(
            name='OperacionCobroSalon',
            fields=[
                ('operacion_id', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('mesa', models.CharField(max_length=10)),
                ('tipo_pago', models.CharField(max_length=30)),
                ('firma', models.CharField(max_length=64)),
                ('respuesta', models.JSONField(default=dict)),
                ('fecha', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Cobro idempotente de salón',
                'verbose_name_plural': 'Cobros idempotentes de salón',
            },
        ),
    ]
