from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pedidos', '0011_opinioncliente'),
    ]

    operations = [
        migrations.CreateModel(
            name='Mozo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, unique=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['nombre'],
            },
        ),
        migrations.AddField(
            model_name='opinioncliente',
            name='mozo',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
