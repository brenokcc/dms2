# -*- coding: utf-8 -*-

from django.conf.urls import include
from django.urls import path

urlpatterns = [
    path('api/', include('dms2.urls')),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
]
