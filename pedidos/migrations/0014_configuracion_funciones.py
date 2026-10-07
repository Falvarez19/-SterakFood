from datetime import time
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('pedidos', '0013_pedido_mozo'),
    ]

    operations = [
        migrations.AddField(model_name='configuracion', name='descuento_efectivo_activo', field=models.BooleanField(default=True, verbose_name='Descuento en efectivo')),
        migrations.AddField(model_name='configuracion', name='descuento_efectivo_porcentaje', field=models.PositiveSmallIntegerField(default=10, verbose_name='Porcentaje de descuento')),
        migrations.AddField(model_name='configuracion', name='cierre_automatico_activo', field=models.BooleanField(default=False, verbose_name='Cierre automático')),
        migrations.AddField(model_name='configuracion', name='hora_cierre', field=models.TimeField(default=time(23, 0), verbose_name='Hora de cierre')),
        migrations.AddField(model_name='configuracion', name='mostrar_promociones', field=models.BooleanField(default=True, verbose_name='Mostrar promociones')),
        migrations.AddField(model_name='configuracion', name='mostrar_opiniones', field=models.BooleanField(default=True, verbose_name='Mostrar opiniones')),
        migrations.AddField(model_name='configuracion', name='mostrar_google_reviews', field=models.BooleanField(default=True, verbose_name='Mostrar Google Reviews')),
        migrations.AddField(model_name='configuracion', name='mostrar_bienvenida', field=models.BooleanField(default=False, verbose_name='Mostrar bienvenida')),
        migrations.AddField(model_name='configuracion', name='salon_habilitado', field=models.BooleanField(default=True, verbose_name='Módulo Salón / Mesas')),
        migrations.AlterField(model_name='configuracion', name='buffet_habilitado', field=models.BooleanField(default=True, verbose_name='Aceptar pedidos online')),
    ]
