from django.urls import re_path

from . import views

app_name = 'docgen'

urlpatterns = [

    # I. Создание документа через форму

    re_path(r'^create/(?P<template_name>\w+)/ie-client/$',                     views.create, name='create_ie',         kwargs={'client_type': 'ie'}),
    re_path(r'^create/(?P<template_name>\w+)/le-client/$',                     views.create, name='create_le',         kwargs={'client_type': 'le'}),
    re_path(r'^create/(?P<template_name>\w+)/ie-client/(?P<object_id>\d+)/$',  views.create, name='create_ie_client',  kwargs={'client_type': 'ie', 'object_type': 'client'}),
    re_path(r'^create/(?P<template_name>\w+)/le-client/(?P<object_id>\d+)/$',  views.create, name='create_le_client',  kwargs={'client_type': 'le', 'object_type': 'client'}),
    re_path(r'^create/(?P<template_name>\w+)/ie-account/(?P<object_id>\d+)/$', views.create, name='create_ie_account', kwargs={'client_type': 'ie', 'object_type': 'account'}),
    re_path(r'^create/(?P<template_name>\w+)/le-account/(?P<object_id>\d+)/$', views.create, name='create_le_account', kwargs={'client_type': 'le', 'object_type': 'account'}),
    re_path(r'^create/task/(?P<object_id>\d+)/$',                              views.create, name='create_task',       kwargs={'object_type': 'task'}),

    # II. Создание документа через фильтр

    # Открытие документа, созданного через форму или фильтр
    re_path(r'^open/$',                  views.open, name='open'),
    re_path(r'^open/(?P<task_id>\d+)/$', views.open, name='open_task'),

    # III. Генерация документа по статичным данным из базы

    re_path(r'^generate/(?P<template_name>\w+)/ie-client/$',                      views.generate, name='generate_ie',         kwargs={'client_type': 'ie'}),
    re_path(r'^generate/(?P<template_name>\w+)/le-client/$',                      views.generate, name='generate_le',         kwargs={'client_type': 'le'}),
    re_path(r'^generate/(?P<template_name>\w+)/ie-client/(?P<client_id>\d+)/$',   views.generate, name='generate_ie_client',  kwargs={'client_type': 'ie'}),
    re_path(r'^generate/(?P<template_name>\w+)/le-client/(?P<client_id>\d+)/$',   views.generate, name='generate_le_client',  kwargs={'client_type': 'le'}),
    re_path(r'^generate/(?P<template_name>\w+)/ie-account/(?P<account_id>\d+)/$', views.generate, name='generate_ie_account', kwargs={'client_type': 'ie'}),
    re_path(r'^generate/(?P<template_name>\w+)/le-account/(?P<account_id>\d+)/$', views.generate, name='generate_le_account', kwargs={'client_type': 'le'}),

]
