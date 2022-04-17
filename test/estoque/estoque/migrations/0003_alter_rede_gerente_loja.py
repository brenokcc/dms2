# Generated by Django 4.0.4 on 2022-04-16 21:28

from django.db import migrations, models
import django.db.models.deletion
import sloth.core.base
import sloth.db.models


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0002_pessoa_rede_gerente'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rede',
            name='gerente',
            field=sloth.db.models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='estoque.pessoa', verbose_name='Gerente'),
        ),
        migrations.CreateModel(
            name='Loja',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', sloth.db.models.CharField(max_length=255, verbose_name='Nome')),
                ('rede', sloth.db.models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='estoque.rede', verbose_name='Rede')),
            ],
            options={
                'verbose_name': 'Loja',
                'verbose_name_plural': 'Lojas',
            },
            bases=(models.Model, sloth.core.base.ModelMixin),
        ),
    ]
