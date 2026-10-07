from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pedidos', '0012_mozo_opinioncliente_mozo'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedido',
            name='mozo',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
