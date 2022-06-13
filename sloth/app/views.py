# -*- coding: utf-8 -*-
import json
import requests
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib import auth, messages
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from sloth.api.tokes import account_activation_token

from .templatetags.tags import is_ajax
from ..core import views
from ..actions import Action, LoginForm, PasswordForm

from ..utils.icons import bootstrap, materialicons, fontawesome
from ..exceptions import JsonReadyResponseException, HtmlJsonReadyResponseException, ReadyResponseException
from . import dashboard


def view(func):
    def decorate(request, *args, **kwargs):
        if request.user.is_authenticated and settings.SLOTH.get('FORCE_PASSWORD_DEFINITION') == True and settings.SLOTH.get('DEFAULT_PASSWORD'):
            default_password = settings.SLOTH['DEFAULT_PASSWORD'](request.user)
            if request.user.check_password(default_password):
                message = 'Altere sua senha padrão'
                messages.warning(request, message)
                return HttpResponseRedirect('/app/password/')
        try:
            # import time; time.sleep(0.5)
            response = func(request, *args, **kwargs)
            response["X-Frame-Options"] = "SAMEORIGIN"
            return response
        except ReadyResponseException as error:
            return error.response
        except JsonReadyResponseException as error:
            return JsonResponse(error.data)
        except HtmlJsonReadyResponseException as error:
            app_messages = render_to_string('app/messages.html', request=request)
            return HttpResponse(app_messages + error.html)
        except PermissionDenied:
            return HttpResponseForbidden()
        except BaseException as error:
            raise error

    return decorate


def context(request, **kwargs):
    kwargs.update(settings=settings)
    if request.user.is_authenticated:
        if request.path.startswith('/app/') and not is_ajax(request):
            if 'stack' not in request.session:
                request.session['stack'] = []
            if request.path == '/app/':
                request.session['stack'].clear()
                request.session['stack'].append(request.path)
            elif request.path in request.session['stack']:
                index = request.session['stack'].index(request.path)
                request.session['stack'] = request.session['stack'][0:index + 1]
            else:
                request.session['stack'].append(request.path)
            request.session.save()
            referrer = request.session['stack'][-2] if len(request.session['stack']) > 1 else None
            return dict(referrer=referrer, **kwargs)
    return kwargs


def manifest(request):
    return JsonResponse(
        {
            "name": settings.SLOTH['NAME'],
            "short_name": settings.SLOTH['NAME'],
            "lang": settings.LANGUAGE_CODE,
            "start_url": "/",
            "scope": "/",
            "display": "standalone",
            "icons": [{
                "src": settings.SLOTH['ICON'],
                "sizes": "192x192",
                "type": "image/png"
            }]
        },
        headers={'Cache-Control': 'public, max-age=31557600'}
    )


def icons(request):
    libraries = {}
    libraries['Bootstrap'] = bootstrap.ICONS
    if 'materialicons' in settings.SLOTH.get('ICONS', ()):
        libraries['Material Icons'] = materialicons.ICONS
    if 'fontawesome' in settings.SLOTH.get('ICONS', ()):
        libraries['Font Awesome'] = fontawesome.ICONS
    return render(
        request, ['app/icons.html'],
        dict(settings=settings, libraries=libraries)
    )


def icon(request):
    return HttpResponseRedirect(
        settings.SLOTH['ICON'] or '/static/images/icon.png'
    )


def favicon(request):
    return HttpResponseRedirect(
        settings.SLOTH['FAVICON'] or '/static/images/icon.png'
    )


def login(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('/app/')
    form = LoginForm(request=request)
    if form.is_valid():
        form.submit()
        if request.user.is_superuser or settings.SLOTH['ROLES']['ALLOW_MULTIPLE']:
            return HttpResponseRedirect('/app/')
        else:
            if request.user.roles.filter(active=True).count() == 1:
                return HttpResponseRedirect('/app/')
            else:
                request.user.roles.update(active=False)
                return HttpResponseRedirect('/app/roles/')
    return render(request, ['app/login.html'], context(request, form=form))


def oauth_login(request, provider_name):
    provider = settings.SLOTH['OAUTH_LOGIN'][provider_name.upper()]
    authorize_url = '{}?response_type=code&client_id={}&redirect_uri={}'.format(
        provider['AUTHORIZE_URL'], provider['CLIENTE_ID'], provider['REDIRECT_URI']
    )
    if 'code' in request.GET:
        access_token_request_data = dict(
            grant_type='authorization_code', code=request.GET.get('code'), redirect_uri=provider['REDIRECT_URI'],
            client_id=provider['CLIENTE_ID'], client_secret=provider['CLIENT_SECRET']
        )
        data = json.loads(
            requests.post(provider['ACCESS_TOKEN_URL'], data=access_token_request_data, verify=False).text
        )
        headers = {
            'Authorization': 'Bearer {}'.format(data.get('access_token')), 'x-api-key': provider['CLIENT_SECRET']
        }

        if provider.get('USER_DATA_METHOD', 'GET').upper() == 'POST':
            data = json.loads(requests.post(provider['USER_DATA_URL'], data={'scope': data.get('scope')}, headers=headers).text)
        else:
            data = json.loads(requests.get(provider['USER_DATA_URL'], data={'scope': data.get('scope')}, headers=headers).text)
        user = User.objects.filter(username=data[provider['USER_DATA']['USERNAME']]).first()
        if user is None:
            user = User.objects.create(
                username=data[provider['USER_DATA']['USERNAME']],
                email=data[provider['USER_DATA']['EMAIL']] if provider['USER_DATA']['EMAIL'] else '',
                first_name=data[provider['USER_DATA']['FIRST_NAME']] if provider['USER_DATA']['FIRST_NAME'] else '',
                last_name=data[provider['USER_DATA']['LAST_NAME']] if provider['USER_DATA']['LAST_NAME'] else ''
            )
        auth.login(request, user)
        return HttpResponseRedirect('/app/')
    else:
        return HttpResponse('<html><script>document.location.href="{}";</script></html>'.format(authorize_url))


def password(request):
    form = PasswordForm(request=request)
    if form.is_valid():
        form.submit()
        return HttpResponseRedirect('..')
    return render(request, ['app/default.html'], context(request, form=form))


def logout(request):
    request.session.clear()
    auth.logout(request)
    return HttpResponseRedirect('/')


def account_activate(request, uid64, token):
    uid = force_str(urlsafe_base64_decode(uid64))
    user = get_object_or_404(User, pk=uid)
    if user is not None and account_activation_token.check_token(user, token):
        form = PasswordForm(request=request, user=user)
        if form.is_valid():
            form.submit()
            user.is_active = True
            user.save()
            auth.login(request, user)
            return HttpResponseRedirect('/app/')
        return render(request, ['app/default.html'], context(request, form=form))

    messages.warning(request, "Link de ativação inválido")
    return HttpResponseRedirect('/')


def index(request):
    return HttpResponseRedirect('/app/')


@view
def app(request):
    request.COOKIES.get('width')
    if request.user.is_authenticated:
        return render(
            request, [getattr(settings, 'INDEX_TEMPLATE', 'app/index.html')],
            context(request, dashboard=dashboard.Dashboards(request))
        )
    return HttpResponseRedirect('/app/login/')

@view
def roles(request):
    if 'names' in request.GET:
        names = request.GET['names'].split('|')
        request.user.roles.update(active=False)
        request.user.roles.filter(name__in=names).update(active=True)
        if len(names) == 1:
            message = 'Perfil "{}" ativado com sucesso.'.format(names[0])
        else:
            message = 'Perfis "{}" ativos com sucesso'.format(', '.join(names))
        messages.success(request, message)
        return HttpResponseRedirect('/app/')
    return render(request, ['app/roles.html'], context(request))


@view
def action(request, name):
    form = views.action(request, name)
    if form.check_permission(request.user):
        ctx = context(request, dashboard=dashboard.Dashboards(request), form=form)
        if form.response:
            return HttpResponse(form.html())
        return render(request, ['app/default.html'], ctx)
    raise PermissionDenied()


@view
def dispatcher(request, app_label, model_name, x=None, y=None, z=None, w=None, k=None):
    ctx = context(request, dashboard=dashboard.Dashboards(request))
    data = views.dispatcher(request, app_label, model_name, x=None if x == 'all' else x, y=y, z=z, w=w, k=k)
    if isinstance(data, Action):
        ctx.update(form=data)
        if data.response:
            return HttpResponse(data.html())
    else:
        ctx.update(data=data)
    return render(request, ['app/default.html'], ctx)
