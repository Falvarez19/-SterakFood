from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('pedidos', '0018_fiscal_preparacion')]
    operations = [migrations.CreateModel(
        name='RespaldoMesasLocal',
        fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('version', models.PositiveBigIntegerField(default=0)),
            ('datos', models.JSONField(default=dict)),
            ('modificado', models.DateTimeField(auto_now=True)),
        ],
        options={'verbose_name': 'Respaldo de mesas local'},
    )]
