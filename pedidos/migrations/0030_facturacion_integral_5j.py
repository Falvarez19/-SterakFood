from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[('pedidos','0029_configuracion_mesas_visibles')]
    operations=[
        migrations.AddField(model_name='facturafiscal',name='receptor_tipo_documento',field=models.PositiveSmallIntegerField(default=99)),
        migrations.AddField(model_name='facturafiscal',name='receptor_numero_documento',field=models.CharField(max_length=20,default='0')),
        migrations.AddField(model_name='facturafiscal',name='receptor_condicion_iva',field=models.PositiveSmallIntegerField(default=5)),
        migrations.AddField(model_name='facturafiscal',name='receptor_nombre',field=models.CharField(max_length=150,blank=True,default='')),
        migrations.AddField(model_name='facturafiscal',name='origen',field=models.CharField(max_length=20,choices=[('salon','Salón'),('para_llevar','Para llevar')],default='salon')),
        migrations.AddField(model_name='facturafiscal',name='origen_pedido',field=models.ForeignKey(to='pedidos.pedido',on_delete=django.db.models.deletion.PROTECT,blank=True,null=True)),
    ]
