from .db.models import ModelMixin, QuerySet, BaseManager, Manager
from .forms import Form, ModelForm, QuerySetForm
from django import forms
from django.db import models
from django.db.models import base

old = base.ModelBase.__new__


def __new__(mcs, name, bases, attrs, **kwargs):

    if attrs['__module__'] != '__fake__':
        fromlist = list(map(str, attrs['__module__'].split('.')))
        module = __import__(attrs['__module__'], fromlist=fromlist)
        if hasattr(module, '{}Set'.format(name)):
            queryset_class = getattr(module, '{}Set'.format(name))
            attrs.update(objects=BaseManager.from_queryset(queryset_class)())
        if 'objects' not in attrs:
            if not all(['objects' in dir(cls) for cls in bases]):
                attrs.update(objects=BaseManager.from_queryset(QuerySet)())

    if bases == (base.Model,):
        bases = base.Model, ModelMixin
    return old(mcs, name, bases, attrs, **kwargs)


class CharField(models.CharField):
    def __init__(self, *args, max_length=255, **kwargs):
        super().__init__(*args, max_length=max_length, **kwargs)


class ForeignKey(models.ForeignKey):
    def __init__(self, to, on_delete=models.CASCADE, **kwargs):
        super().__init__(to=to, on_delete=on_delete, **kwargs)


class OneToOneField(models.OneToOneField):
    def __init__(self, to, on_delete=models.CASCADE, **kwargs):
        super().__init__(to=to, on_delete=on_delete, **kwargs)


base.ModelBase.__new__ = __new__
models.QuerySet = QuerySet
models.Manager = Manager
models.CharField = CharField
models.ForeignKey = ForeignKey
models.OneToOneField = OneToOneField
forms.Form = Form
forms.ModelForm = ModelForm
forms.QuerySetForm = QuerySetForm


