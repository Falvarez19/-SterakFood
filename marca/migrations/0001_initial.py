from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='MarcaNegocio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(default='SterakFood', max_length=90)),
                ('nombre_corto', models.CharField(default='SterakFood', max_length=45)),
                ('subtitulo', models.CharField(blank=True, default='', max_length=160)),
                ('color_principal', models.CharField(default='#FF6600', max_length=7)),
                ('color_secundario', models.CharField(default='#FF6600', max_length=7)),
                ('color_acento', models.CharField(default='#FF8533', max_length=7)),
                ('colores_personalizados', models.BooleanField(default=False)),
                ('logo_png', models.BinaryField(blank=True, editable=False, null=True)),
                ('logo_claro_png', models.BinaryField(blank=True, editable=False, null=True)),
                ('actualizado', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Personalización del negocio',
                'verbose_name_plural': 'Personalización del negocio',
            },
        )
    ]
