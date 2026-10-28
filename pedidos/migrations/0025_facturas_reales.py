from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('pedidos', '0024_evento_sync_pos_offline')]
    operations = [
        migrations.CreateModel(
            name='FacturaFiscal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado',models.CharField(choices=[('pendiente','Pendiente de solicitar'),('incierto','Verificar en ARCA antes de reintentar'),('autorizada','Autorizada con CAE'),('rechazada','Rechazada por ARCA')],default='pendiente',max_length=16,db_index=True)),
                ('entorno',models.CharField(max_length=20)),
                ('cuit_emisor',models.CharField(max_length=11)),
                ('punto_venta',models.PositiveIntegerField()),
                ('tipo_comprobante',models.PositiveSmallIntegerField(default=6)),
                ('numero',models.PositiveIntegerField(blank=True,null=True)),
                ('fecha_comprobante',models.CharField(max_length=8,blank=True)),
                ('total',models.DecimalField(max_digits=12,decimal_places=2)),
                ('neto_21',models.DecimalField(max_digits=12,decimal_places=2,default=0)),
                ('iva_21',models.DecimalField(max_digits=12,decimal_places=2,default=0)),
                ('cae',models.CharField(max_length=20,blank=True)),
                ('vencimiento_cae',models.CharField(max_length=8,blank=True)),
                ('url_qr',models.TextField(blank=True)),
                ('observaciones',models.TextField(blank=True)),
                ('impresion_confirmada',models.BooleanField(db_index=True,default=False)),
                ('fecha_impresion',models.DateTimeField(blank=True,null=True)),
                ('creado',models.DateTimeField(auto_now_add=True)),
                ('actualizado',models.DateTimeField(auto_now=True)),
                ('borrador',models.OneToOneField(on_delete=django.db.models.deletion.PROTECT,related_name='factura_real',to='pedidos.borradorfiscal')),
            ],
            options={'ordering':['-creado']},
        ),
        migrations.AddConstraint(model_name='facturafiscal', constraint=models.UniqueConstraint(
            fields=('entorno','cuit_emisor','punto_venta','tipo_comprobante','numero'), name='unica_factura_arca_numero')),
    ]
