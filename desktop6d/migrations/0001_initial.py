from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(name='AjustesDesktop6D', fields=[
            ('id', models.BigAutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
            ('impresion_activa', models.BooleanField(default=False)),
            ('actualizado', models.DateTimeField(auto_now=True)),
        ]),
        migrations.CreateModel(name='ImpresionLocal6D', fields=[
            ('id', models.BigAutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
            ('tipo', models.CharField(choices=[('pedido','Pedido'),('cuenta','Comprobante cuenta corriente')], max_length=12)),
            ('referencia_id', models.PositiveIntegerField()),
            ('destino', models.CharField(choices=[('cocina','Cocina'),('barra','Barra'),('caja','Caja')], max_length=10)),
            ('estado', models.CharField(choices=[('pendiente','Pendiente'),('enviando','Enviando'),('enviado','Enviado a dispositivo'),('incierto','Resultado incierto')], default='pendiente', max_length=10)),
            ('intentos', models.PositiveSmallIntegerField(default=0)),
            ('ultimo_error', models.CharField(blank=True, default='', max_length=400)),
            ('creado', models.DateTimeField(auto_now_add=True)),
            ('actualizado', models.DateTimeField(auto_now=True)),
        ], options={'ordering':['-actualizado']}),
        migrations.AddConstraint(model_name='impresionlocal6d', constraint=models.UniqueConstraint(fields=('tipo','referencia_id','destino'), name='desktop6d_impresion_unica')),
    ]
