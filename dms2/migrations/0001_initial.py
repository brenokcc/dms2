# Generated by Django 3.2.8 on 2021-10-20 19:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import dms2.db.models
import oauth2_provider.generators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Scope',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', dms2.db.models.CharField(max_length=50, verbose_name='Nome')),
                ('description', models.TextField(verbose_name='Descrição')),
            ],
            options={
                'verbose_name': 'Escopo',
                'verbose_name_plural': 'Escopos',
            },
            bases=(models.Model, dms2.base.ModelMixin),
        ),
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('client_id', dms2.db.models.CharField(db_index=True, default=oauth2_provider.generators.generate_client_id, max_length=100, unique=True)),
                ('redirect_uris', models.TextField(blank=True, help_text='Allowed URIs list, space separated')),
                ('client_type', dms2.db.models.CharField(choices=[('confidential', 'Confidential'), ('public', 'Public')], max_length=32)),
                ('authorization_grant_type', dms2.db.models.CharField(choices=[('authorization-code', 'Authorization code'), ('implicit', 'Implicit'), ('password', 'Resource owner password-based'), ('client-credentials', 'Client credentials'), ('openid-hybrid', 'OpenID connect hybrid')], max_length=32)),
                ('client_secret', dms2.db.models.CharField(blank=True, db_index=True, default=oauth2_provider.generators.generate_client_secret, max_length=255)),
                ('name', dms2.db.models.CharField(blank=True, max_length=255)),
                ('skip_authorization', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('algorithm', dms2.db.models.CharField(blank=True, choices=[('', 'No OIDC support'), ('RS256', 'RSA with SHA-2 256'), ('HS256', 'HMAC with SHA-2 256')], default='', max_length=5)),
                ('available_scopes', models.ManyToManyField(blank=True, related_name='s1', to='dms2.Scope')),
                ('default_scopes', models.ManyToManyField(blank=True, related_name='s2', to='dms2.Scope')),
                ('user', dms2.db.models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dms2_application', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Aplicação',
                'verbose_name_plural': 'Aplicações',
            },
            bases=(models.Model, dms2.base.ModelMixin),
        ),
    ]
