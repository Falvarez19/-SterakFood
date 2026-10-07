from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pedidos', '0009_producto_codigo_rapido'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='en_promocion',
            field=models.BooleanField(default=False, verbose_name='Mostrar en Promos'),
        ),
    ]
