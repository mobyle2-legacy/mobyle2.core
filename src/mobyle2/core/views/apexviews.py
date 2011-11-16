#!/usr/bin/env python
# -*- coding: utf-8 -*-

from apex import views as av
from mobyle2.core.views import get_base_params

from pyramid.httpexceptions import HTTPFound

def wrap_view(view, request):
    params = view(request)
    if not isinstance(params, HTTPFound):
        params.update(get_base_params(request=request))
        login_params = params['login_params']
        params['velruse_forms'] = login_params.get('velruse_forms', None)
        params['self_register'] = login_params.get('self_register', None)
        params['include_came_from'] =  login_params.get('include_came_from', None)
    return params

def login(request):
    return wrap_view(av.login, request)

def register(request):
    return wrap_view(av.register, request)

