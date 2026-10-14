from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('pedidos', '0016_movimiento_cuenta_pos_operacion_id')]

    operations = [
        migrations.CreateModel(
            name='ComprobanteCuentaCorriente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(default='consumo', max_length=20)),
                ('cliente_nombre', models.CharField(max_length=120)),
                ('mesa', models.CharField(blank=True, default='', max_length=20)),
                ('mozo', models.CharField(blank=True, default='', max_length=100)),
                ('items', models.JSONField(default=list)),
                ('total', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('saldo_anterior', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('saldo_posterior', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('cuenta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comprobantes', to='pedidos.cuentacorriente')),
                ('movimiento', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='comprobante_pos', to='pedidos.movimientocuentacorriente')),
            ],
            options={'verbose_name': 'Comprobante de cuenta corriente', 'verbose_name_plural': 'Comprobantes de cuenta corriente', 'ordering': ['-fecha']},
        ),
        migrations.CreateModel(
            name='ImpresionComprobanteCuenta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('impreso', models.BooleanField(default=False)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_impreso', models.DateTimeField(blank=True, null=True)),
                ('comprobante', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='impresiones', to='pedidos.comprobantecuentacorriente')),
            ],
            options={'verbose_name': 'Impresión pendiente de cuenta', 'verbose_name_plural': 'Impresiones pendientes de cuenta', 'ordering': ['fecha_creacion', 'id']},
        ),
    ]
