# Generated as a standalone first step for the fiscal migration.
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    dependencies = [('pedidos', '0017_comprobantes_cuenta_corriente')]

    operations = [
        migrations.CreateModel(
            name='ConfiguracionFiscal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('razon_social', models.CharField(blank=True, default='', max_length=180)),
                ('cuit', models.CharField(blank=True, default='', max_length=11)),
                ('condicion_iva', models.CharField(choices=[('ri','Responsable inscripto'),('monotributo','Monotributista'),('exento','Exento'),('otro','Otra condición')],default='ri',max_length=20)),
                ('punto_venta_referencia', models.PositiveIntegerField(blank=True, help_text='Solo referencia del sistema anterior. No asigna ni habilita un punto de venta en ARCA.', null=True)),
                ('domicilio_fiscal', models.CharField(blank=True, default='', max_length=220)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name':'Configuración fiscal (preparación)','verbose_name_plural':'Configuración fiscal (preparación)'},
        ),
        migrations.CreateModel(
            name='BorradorFiscal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('operacion_id', models.UUIDField(editable=False,unique=True)),
                ('mesa', models.CharField(max_length=10)),
                ('mozo', models.CharField(blank=True, default='', max_length=100)),
                ('items', models.JSONField(default=list)),
                ('total_estimado', models.DecimalField(decimal_places=2,max_digits=12)),
                ('estado', models.CharField(default='borrador',editable=False,max_length=20)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name':'Borrador fiscal NO EMITIDO','verbose_name_plural':'Borradores fiscales NO EMITIDOS','ordering':['-fecha_creacion']},
        ),
    ]
