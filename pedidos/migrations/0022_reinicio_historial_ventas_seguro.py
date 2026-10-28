# v155: non-destructive reset of displayed sales/history.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('pedidos', '0021_alter_estadosyncqr_id_alter_pedidoqrremoto_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedido',
            name='archivado_ventas',
            field=models.BooleanField(default=False, db_index=True),
        ),
        migrations.CreateModel(
            name='CorteHistorialVentas',
            fields=[
                ('id', models.BigAutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('cantidad_pedidos', models.PositiveIntegerField(default=0)),
                ('total_archivado', models.DecimalField(default=0, max_digits=14, decimal_places=2)),
                ('origen', models.CharField(default='panel', max_length=40)),
            ],
            options={
                'ordering': ['-fecha', '-id'],
                'verbose_name': 'Reinicio de historial de ventas',
                'verbose_name_plural': 'Reinicios de historial de ventas',
            },
        ),
        migrations.AddField(
            model_name='pedido',
            name='corte_ventas',
            field=models.ForeignKey(
                to='pedidos.cortehistorialventas',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='pedidos_archivados', null=True, blank=True,
            ),
        ),
    ]
