# Generated by Django 3.2.8 on 2021-10-17 20:57

from django.db import migrations, models
import django.db.models.deletion
import dms2
import dms2.db.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Endereco',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('logradouro', dms2.CharField(max_length=255, verbose_name='Logradouro')),
                ('numero', dms2.CharField(max_length=255, verbose_name='Número')),
            ],
            options={
                'verbose_name': 'Endereço',
                'verbose_name_plural': 'Endereços',
            },
            bases=(models.Model, dms2.db.models.ModelMixin),
        ),
        migrations.CreateModel(
            name='Estado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sigla', dms2.CharField(max_length=255, verbose_name='Sigla')),
            ],
            options={
                'verbose_name': 'Estado',
                'verbose_name_plural': 'Estado',
            },
            bases=(models.Model, dms2.db.models.ModelMixin),
        ),
        migrations.CreateModel(
            name='Servidor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('matricula', dms2.CharField(max_length=255, verbose_name='Matrícula')),
                ('nome', dms2.CharField(max_length=255, verbose_name='Nome')),
                ('cpf', dms2.CharField(max_length=255, verbose_name='CPF')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
                ('endereco', dms2.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='base.endereco', verbose_name='Endereço')),
            ],
            options={
                'verbose_name': 'Servidor',
                'verbose_name_plural': 'Servidores',
            },
            bases=(models.Model, dms2.db.models.ModelMixin),
        ),
        migrations.CreateModel(
            name='Municipio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', dms2.CharField(max_length=255, verbose_name='Nome')),
                ('estado', dms2.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.estado', verbose_name='Estado')),
            ],
            options={
                'verbose_name': 'Municipio',
                'verbose_name_plural': 'Municipios',
            },
            bases=(models.Model, dms2.db.models.ModelMixin),
        ),
        migrations.CreateModel(
            name='Frequencia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('horario', models.DateTimeField(verbose_name='Horário')),
                ('homologado', models.BooleanField(default=False, verbose_name='Homologado')),
                ('servidor', dms2.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.servidor', verbose_name='Servidor')),
            ],
            options={
                'verbose_name': 'Frequência',
                'verbose_name_plural': 'Frequências',
            },
            bases=(models.Model, dms2.db.models.ModelMixin),
        ),
        migrations.CreateModel(
            name='Ferias',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ano', models.IntegerField(verbose_name='Ano')),
                ('inicio', models.DateField(verbose_name='Início')),
                ('fim', models.DateField(verbose_name='Fim')),
                ('servidor', dms2.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.servidor', verbose_name='Servidor')),
            ],
            options={
                'verbose_name': 'Férias',
                'verbose_name_plural': 'Férias',
            },
            bases=(models.Model, dms2.db.models.ModelMixin),
        ),
        migrations.AddField(
            model_name='endereco',
            name='municipio',
            field=dms2.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.municipio', verbose_name='Município'),
        ),
    ]
