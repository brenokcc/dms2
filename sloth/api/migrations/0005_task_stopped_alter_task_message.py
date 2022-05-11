# Generated by Django 4.0.4 on 2022-05-11 18:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_task'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='stopped',
            field=models.BooleanField(default=False, verbose_name='Interrompida'),
        ),
        migrations.AlterField(
            model_name='task',
            name='message',
            field=models.CharField(max_length=255, null=True, verbose_name='Mensagem'),
        ),
    ]
