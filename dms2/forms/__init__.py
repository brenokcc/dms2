# -*- coding: utf-8 -*-
from functools import lru_cache

from django.forms import *
from django.forms import widgets
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.template.loader import render_to_string


class FormMixin:

    def serialize(self, wrap=False, verbose=False):
        if self.message:
            return self.message
        if wrap:
            data = dict(type='form')
            form_fields = {}
            for field_name in self.fields:
                field = self.fields[field_name]
                form_fields[field_name] = dict(
                    label=field.label,
                    name=field_name,
                    type=type(field).__name__.replace('Field', '').lower(),
                    required=field.required,
                    value=self.data.get(field_name)
                )
            data.update(self.get_metadata())
            data.update(fields=form_fields, errors=self.errors)
            return data
        return {}

    @classmethod
    @lru_cache
    def get_metadata(cls, path=None):
        form_name = cls.__name__
        meta = getattr(cls, 'Meta', None)
        name = form_name
        target = 'model'
        icon = None
        style = 'primary'
        method = 'get'
        batch = False
        if meta:
            name = getattr(meta, 'name', form_name)
            icon = getattr(meta, 'icon', None)
            style = getattr(meta, 'style', 'primary')
            method = getattr(meta, 'method', 'post')
            batch = getattr(meta, 'batch', False)
        if path:
            if hasattr(cls, 'instances'):
                target = 'queryset' if batch else 'instance'
                path = '{}{{id}}/{}/'.format(path, form_name)
            else:
                path = '{}{}/'.format(path, form_name)
        metadata = dict(type='form', name=name, target=target)
        if getattr(meta, 'batch', False):
            metadata.update(batch=True)
        metadata.update(method=method, icon=icon, style=style, path=path)
        return metadata

    def get_method(self):
        meta = getattr(self, 'Meta', None)
        return getattr(meta, 'method', 'post') if meta else 'post'

    def has_permission(self, user):
        return self and user.is_superuser

    def has_add_permission(self, user):
        return self.instance and self.instance.has_add_permission(user)

    def has_edit_permission(self, user):
        return self.instance and self.instance.has_edit_permission(user)

    def has_delete_permission(self, user):
        return self.instance and self.instance.has_add_permission(user)

    def __str__(self):
        for field in self.fields.values():
            classes = field.widget.attrs.get('class', '').split()
            if isinstance(field.widget, widgets.TextInput):
                classes.append('form-control')
            elif isinstance(field.widget, widgets.Select):
                classes.append('form-control')
            elif isinstance(field.widget, widgets.CheckboxInput):
                classes.append('form-check-input')

            if isinstance(field, DateField):
                classes.append('date-input')

            if getattr(field.widget, 'mask', None):
                classes.append('masked-input')
                field.widget.attrs['data-reverse'] = 'false'
                field.widget.attrs['data-mask'] = getattr(field.widget, 'mask')
            if getattr(field.widget, 'rmask', None):
                classes.append('masked-input')
                field.widget.attrs['data-reverse'] = 'true'
                field.widget.attrs['data-mask'] = getattr(field.widget, 'rmask')
            field.widget.attrs['class'] = ' '.join(classes)
        return mark_safe(
            render_to_string(['adm/form.html'], dict(self=self), request=self.request)
        )

    def notify(self, text='Ação realizada com sucesso', style='sucess', **kwargs):
        messages.add_message(self.request, messages.INFO, text)
        self.message = dict(type='message', text=text, style=style, **kwargs)


class Form(FormMixin, Form):
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        self.message = None
        self.instantiator = kwargs.pop('instantiator', None)
        self.request = kwargs.pop('request', None)
        if 'data' not in kwargs:
            if self.base_fields:
                data = self.request.POST or None
            else:
                data = self.request.POST
            kwargs['data'] = data
        super().__init__(*args, **kwargs)

    def process(self):
        self.notify()


class ModelForm(FormMixin, ModelForm):

    def __init__(self, *args, **kwargs):
        self.message = None
        self.request = kwargs.pop('request', None)
        self.instantiator = kwargs.pop('instantiator', None)
        if 'data' not in kwargs:
            if self.base_fields:
                data = self.request.POST or None
            else:
                data = self.request.POST
            kwargs['data'] = data
        super().__init__(*args, **kwargs)

    def process(self):
        self.save()
        self.notify()


class QuerySetForm(ModelForm):
    instances = []

    def __init__(self, *args, **kwargs):
        self.instances = kwargs.pop('instances', ())
        if self.instances:
            kwargs.update(instance=self.instances[0])
        super().__init__(*args, **kwargs)

    def process(self):
        if self.instances:
            for instance in self.instances:
                self.instance = instance
                self._post_clean()
                self.save()
        else:
            self.save()
        self.notify()
