from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('pedidos', '0025_facturas_reales')]

    operations = [
        migrations.CreateModel(
            name='PedidoParaLlevar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('solicitud_id', models.UUIDField(db_index=True, unique=True)),
                ('observaciones', models.TextField(blank=True, default='')),
                ('fecha_cobro', models.DateTimeField(blank=True, null=True)),
                ('pedido', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='para_llevar', to='pedidos.pedido')),
            ],
            options={'verbose_name': 'Pedido para llevar', 'verbose_name_plural': 'Pedidos para llevar'},
        ),
    ]
