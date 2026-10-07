from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pedidos', '0010_producto_en_promocion'),
    ]

    operations = [
        migrations.CreateModel(
            name='OpinionCliente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('atencion', 'Atención'), ('comida', 'Comida'), ('demora', 'Demora'), ('otro', 'Otro')], default='atencion', max_length=20)),
                ('mensaje', models.TextField()),
                ('mesa', models.CharField(blank=True, max_length=20)),
                ('nombre', models.CharField(blank=True, max_length=100)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('leida', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-fecha_creacion'],
            },
        ),
    ]
