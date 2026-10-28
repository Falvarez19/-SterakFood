from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('pedidos', '0026_pedidoparallevar')]
    operations = [
        migrations.AddField(
            model_name='detallepedido', name='aviso_celiaco',
            field=models.BooleanField(default=False),
        ),
    ]
