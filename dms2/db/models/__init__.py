# -*- coding: utf-8 -*-
from uuid import uuid1

import math
import json
import operator

from django.core.exceptions import FieldDoesNotExist
from django.db.models import Q
from functools import reduce
from django.apps import apps
from django.db import models
from django.db.models import manager
from django.forms.models import modelform_factory
from django.template.loader import render_to_string

from dms2.exceptions import ReadyResponseException
from dms2.forms import ModelForm
from dms2.utils import getattrr, serialize
from dms2.db.models.decorators import meta


class ValueSet(dict):
    def __init__(self, instance, names):
        self.model = type(instance)
        self.instance = instance
        self.names = []
        self.actions = []
        for attr_name in names:
            self.names.extend(attr_name) if isinstance(attr_name, tuple) else self.names.append(attr_name)
        super().__init__()

    def allow(self, *names):
        self.actions = list(names)
        return self

    def load(self, wrap=False, verbose=False):
        if self.names:
            metadata = getattr(self.instance, '_meta')
            for attr_name in self.names:
                attr, value = getattrr(self.instance, attr_name)
                path = '/{}/{}/{}/{}/'.format(metadata.app_label, metadata.model_name, self.instance.pk, attr_name)
                if isinstance(value, QuerySet):
                    actions = getattr(value, 'metadata')['actions']
                    verbose_name = getattr(attr, 'verbose_name', attr_name) if verbose else attr_name
                    value = value.serialize(path=path, wrap=wrap, verbose=verbose)
                    if wrap:
                        value['name'] = verbose_name
                elif isinstance(value, ValueSet):
                    actions = getattr(value, 'actions')
                    key = attr_name
                    verbose_name = getattr(attr, 'verbose_name', attr_name) if verbose else attr_name
                    if attr_name == 'fieldset':
                        key = None
                        path = None
                    value.load(wrap=wrap, verbose=verbose)
                    value = dict(type=value.get_type(), name=verbose_name, key=key, actions=[], data=value, path=path) if wrap else value
                else:
                    actions = []
                    value = serialize(value)

                if wrap:
                    for form_name in actions:
                        value['actions'].append(
                            self.instance.action_form_cls(form_name).get_metadata(path)
                        )

                if verbose:
                    self[self.model.get_attr_verbose_name(attr_name)[0]] = value
                else:
                    self[attr_name] = value
        else:
            self['id'] = self.instance.id
            self[self.model.__name__.lower()] = str(self.instance)

    def __str__(self):
        return json.dumps(self, indent=4, ensure_ascii=False)

    def get_type(self):
        for value in self.values():
            if isinstance(value, dict) and value.get('type') in ('queryset', 'fieldset'):
                return 'fieldsets'
        return 'fieldset'

    def cached_data(self, data_type):
        attr_name = '_{}_'.format(data_type)
        if hasattr(type(self.instance), attr_name):
            getattr(type(self.instance), attr_name)
        data = []
        for k, v in type(self.instance).__dict__.items():
            if hasattr(v, data_type) and getattr(v, data_type):
                data.append(k)
        setattr(type(self.instance), attr_name, data)
        return data

    def serialize(self, wrap=False, verbose=False):
        self.load(wrap=wrap, verbose=verbose)
        if wrap:
            data = {}
            names = self.cached_data('primary')
            if names:
                extra = self.instance.values(*names)
                extra.load(wrap=wrap, verbose=verbose)
                data.update(extra)
            data.update(self)
            output = dict(type='object', name=str(self.instance), data=data)
            names = self.cached_data('auxiliary')
            if names:
                extra = self.instance.values(*names)
                extra.load(wrap=wrap, verbose=verbose)
                output.update(auxiliary=extra)
            return output
        else:
            if len(self.names) == 1:
                return self[self.names[0]]
            return self


class QuerySet(models.QuerySet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metadata = dict(
            display=[], filters={}, search=[], ordering=[], paginate=15, actions=[]
        )

    def _clone(self):
        clone = super()._clone()
        clone.metadata = self.metadata
        return clone

    def _get_list_search(self):
        return self.metadata['search']

    def _get_list_display(self):
        if not self.metadata['display']:
            self.metadata['display'] = [
                field.name for field in getattr(self.model, '_meta').fields[0:5]
            ]
        return self.metadata['display']

    def _get_list_filter(self):
        return self.metadata['filters']

    def _get_list_ordering(self):
        return self.metadata['ordering']

    def _get_search(self, verbose=False):
        display = {}
        for lookup in self._get_list_search():
            verbose_name, _ = self.model.get_attr_verbose_name(lookup)
            display[verbose_name if verbose else lookup] = dict(key=lookup, name=verbose_name)
        return display

    def _get_display(self, verbose=False):
        display = {}
        for lookup in self._get_list_display():
            verbose_name, sort = self.model.get_attr_verbose_name(lookup)
            display[verbose_name if verbose else lookup] = dict(key=lookup, name=verbose_name, sort=sort)
        return display

    def _get_filters(self, verbose=False):
        filters = {}
        for lookup in self._get_list_filter():
            field = self.model.get_field(lookup)
            field_type_name = type(field).__name__
            filter_type = 'choices'
            if 'Boolean' in field_type_name:
                filter_type = 'boolean'
            elif 'DateTime' in field_type_name:
                filter_type = 'datetime'
            elif 'Date' in field_type_name:
                filter_type = 'date'
            filters[
                str(field.verbose_name) if verbose else lookup
            ] = dict(key=lookup, name=field.verbose_name, type=filter_type, choices=None)

        ordering = []
        for lookup in self._get_list_ordering():
            field = self.model.get_field(lookup)
            ordering.append(dict(id=lookup, text=field.verbose_name))
        if ordering:
            filters['Ordernação'] = dict(
                key='ordering', name='Ordenação', type='choices', choices=ordering
            )
        return filters

    def to_list(self, verbose=False):
        data = []
        for obj in self:
            data.append(obj.values(*self._get_list_display()).serialize(verbose=verbose))
        return data

    def choices(self, filter_lookup, q=None):
        items = []
        related_model = getattrr(self.model, filter_lookup)[0].field.related_model
        ids = self.values_list(filter_lookup, flat=True).order_by(filter_lookup).distinct()
        qs = related_model.objects.filter(id__in=ids)
        if q:
            lookups = []
            for search_field in ['nome']:
                lookups.append(Q(**{'{}__icontains'.format(search_field): q}))
            qs = qs.filter(reduce(operator.__or__, lookups))
        total = qs.count()
        for obj in qs[0:25]:
            items.append(dict(id=obj.id, text=str(obj)))
        return dict(
            total=total, page=1, pages=math.ceil((1.0 * total) / 25),
            q=q, items=items
        )

    def serialize(self, att_name=None, path=None, wrap=False, verbose=True):
        if wrap:
            attr = getattr(self, att_name or 'all')
            if hasattr(attr, 'verbose_name'):
                verbose_name = getattr(attr, 'verbose_name', att_name)
            else:
                verbose_name = str(getattr(self.model, '_meta').verbose_name)
            search = self._get_search(verbose)
            display = self._get_display(verbose)
            filters = self._get_filters(verbose)
            data = dict(
                uuid=uuid1().hex,
                type='queryset', name=verbose_name, count=self.count(), actions=[],
                metadata=dict(search=search, display=display, filters=filters),
                data=self.to_list(verbose=verbose), path=path
            )
            metadata = getattr(self.model, '_meta')
            path = '/{}/{}/'.format(metadata.app_label, metadata.model_name)
            if att_name:
                path = '{}{}/'.format(path, att_name)

            for form_name in self.metadata['actions']:
                data['actions'].append(
                    self.model.action_form_cls(form_name).get_metadata(path)
                )
            data.update(path=path)
            return data
        return self.to_list()

    def display(self, *names):
        self.metadata['display'] = list(names)
        return self

    def search(self, *names):
        self.metadata['search'] = list(names)
        return self

    def filters(self, *names):
        self.metadata['filters'] = list(names)
        return self

    def ordering(self, *names):
        self.metadata['ordering'] = list(names)
        return self

    def paginate(self, size):
        self.metadata['paginate'] = size
        return self

    def allow(self, *names):
        self.metadata['actions'] = list(names)
        return self

    def html(self):
        data = self.serialize(wrap=True, verbose=True)
        return render_to_string('adm/queryset.html', dict(data=data))

    def contextualize(self, request):
        if 'choices' in request.GET:
            raise ReadyResponseException(
                self.choices(request.GET['choices'])
            )
        return self


class BaseManager(manager.BaseManager):
    def get_queryset(self):
        return super().get_queryset().all()


class Manager(BaseManager.from_queryset(QuerySet)):
    pass


class ModelMixin(object):

    def init_one_to_one_fields(self):
        for field in getattr(self, '_meta').fields:
            if isinstance(field, models.OneToOneField):
                if getattr(self, '{}_id'.format(field.name)) is None:
                    setattr(self, field.name, field.related_model())

    def has_view_permission(self, user):
        return self and user.is_superuser

    def has_attr_view_permission(self, user, name):
        attr = getattr(self, 'has_{}_permission'.format(name), None)
        return attr is None or attr(user)

    def has_add_permission(self, user):
        return self and user.is_superuser

    def has_edit_permission(self, user):
        return self and user.is_superuser

    def has_delete_permission(self, user):
        return self and user.is_superuser

    def values(self, *names):
        return ValueSet(self, names)

    @meta('Dados Gerais')
    def fieldset(self):
        model = type(self)
        names = [field.name for field in getattr(model, '_meta').fields[0:5]]
        return self.values(*names)

    def view(self):
        return self.values('fieldset')

    def serialize(self, wrap=True, verbose=True):
        return self.view().serialize(wrap=wrap, verbose=verbose)

    def get_absolute_url(self, prefix=''):
        return '{}/{}/{}/{}/'.format(prefix, self._meta.app_label, self._meta.model_name, self.pk)

    def __str__(self):
        return '{} #{}'.format(self._meta.verbose_name, self.pk)

    @classmethod
    def add_form_cls(cls):
        return modelform_factory(cls, form=ModelForm, exclude=())

    @classmethod
    def edit_form_cls(cls):
        return modelform_factory(cls, form=ModelForm, exclude=())

    @classmethod
    def delete_form_cls(cls):
        return modelform_factory(cls, form=ModelForm, fields=())

    @classmethod
    def action_form_cls(cls, action):
        config = apps.get_app_config(cls._meta.app_label)
        forms = __import__(
            '{}.forms'.format(config.module.__package__),
            fromlist=config.module.__package__.split()
        )
        for name in dir(forms):
            if name.lower() == action.lower():
                return getattr(forms, name)
        return None

    @classmethod
    def get_field(cls, lookup):
        model = cls
        attrs = lookup.split('__')
        while attrs:
            attr_name = attrs.pop(0)
            if attrs:  # go deeper
                field = getattr(model, '_meta').get_field(attr_name)
                model = field.related_model
            else:
                try:
                    return getattr(model, '_meta').get_field(attr_name)
                except FieldDoesNotExist:
                    pass
        return None

    @classmethod
    def get_attr_verbose_name(cls, lookup):
        field = cls.get_field(lookup)
        if field:
            return str(field.verbose_name), True
        attr = getattr(cls, lookup)
        return getattr(attr, 'verbose_name', lookup), False

    @classmethod
    def get_api_paths(cls):
        instance = cls()
        instance.init_one_to_one_fields()
        url = '/api/{}/{}/'.format(cls._meta.app_label, cls._meta.model_name)

        info = dict()
        info[url] = [('get', 'List', 'List objects', {'type': 'string'})]
        info['{}{{id}}/'.format(url)] = [
            ('get', 'View', 'View object', {'type': 'string'}),
            ('post', 'Add', 'Add object', {'type': 'string'}),
            ('put', 'Edit', 'Edit object', {'type': 'string'}),
        ]
        for name, attr in cls.__dict__.items():
            if hasattr(attr, 'decorated'):
                v = getattr(instance, name)()
                info['{}{{id}}/{}/'.format(url, name)] = [
                    ('get', attr.verbose_name, 'View {}'.format(attr.verbose_name), {'type': 'string'}),
                ]
                if isinstance(v, ValueSet):
                    for action in v.actions:
                        info['{}{{id}}/{}/{{ids}}/{}/'.format(url, name, action)] = [
                            ('post', action, 'Execute {}'.format(action), {'type': 'string'}),
                        ]
                elif isinstance(v, QuerySet):
                    for action in v.metadata['actions']:
                        info['{}{{id}}/{}/{{ids}}/{}/'.format(url, name, action)] = [
                            ('post', action, 'Execute {}'.format(action), {'type': 'string'}),
                        ]

        paths = {}
        for url, data in info.items():
            paths[url] = {}
            for method, summary, description, schema in data:
                paths[url][method] = {
                    'summary': summary,
                    'description': description,
                    'responses': {
                        '200': {'description': 'OK', 'content': {'application/json': {'schema': schema}}}
                    },
                    'tags': [cls._meta.app_label],
                    'security': [dict(OAuth2=[], BasicAuth=[])]  # , BearerAuth=[], ApiKeyAuth=[]
                }
        return paths
