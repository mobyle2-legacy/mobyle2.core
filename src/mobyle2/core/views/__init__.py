#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

from pyramid.url import resource_url, current_route_url
from pyramid.traversal import resource_path, resource_path_tuple, traverse

from pyramid.renderers import get_renderer
from pyramid.renderers import render_to_response, render

from pyramid.threadlocal import get_current_request

from apex import views as apex_views

from mobyle2.core.utils import auto_translate
from mobyle2.core.models.auth import self_registration
from pyramid.httpexceptions import HTTPFound

def get_nav_infos(context, request, default_nav_title=''):
    def t(string):
        return auto_translate(request, string)
    _ = t# for babel
    i = {}
    i['name'] = _(getattr(context, '__description__', default_nav_title))
    i['url'] = resource_url(context, request)
    i['path'] = resource_path(context)
    return i

def get_breadcrumbs(request, context=None):
    breadcrumbs = []
    req = request
    if not context:
        context = request.context
    pathes = resource_path_tuple(context)
    resources = []
    t = request.root
    for i, item in enumerate(pathes):
        t = traverse(t, item)['context']
        resources.append((i, t, item))
    end = len(resources)
    for i, resource, item in resources:
        infos = get_nav_infos(resource, req, item)
        if i == 0:
            infos['class'] = 'start'
        if 0 < i < end-1:
            infos['class'] = 'middle'
        if i == end-1:
            infos['class'] = 'end'
        breadcrumbs.append(infos)
    return breadcrumbs

def get_globaltabs(request, context=None):
    tabs = []
    r = request.root
    req =request
    if not context:
        context = req.context
    current_path = resource_path(context)
    for item in r.items:
        resource = r[item]
        i = get_nav_infos(resource, req, item)
        i['class'] = ''
        if current_path.startswith(i['path']):
            i['class'] += ' selected'
        tabs.append(i)
    return tabs

def get_base_params(view=None,
                    event=None,
                    request=None,
                    breadcrumbs=True,
                    globaltabs=True,
                    main=True,
                    apex=True,
                    login=True,
                    banner=True):
    if event is not None:
        req = event['request']
        view = event['view']
    elif request is not None:
        req = request
    else:
        req = getattr(view, 'request', get_current_request())
    p = {}
    qs = dict(req.GET)
    qs.update(req.POST)
    if apex:
        p['apex_form'] =   get_renderer('apex:templates/forms/tableform.pt').implementation()
        p['apex_template'] =   get_renderer('apex:templates/apex_template.pt').implementation()
    if banner:     p['banner'] =      get_renderer('../templates/includes/banner.pt').implementation()
    if globaltabs: p['globaltabs'] =  get_renderer('../templates/includes/globaltabs.pt').implementation()
    if breadcrumbs:p['breadcrumbs'] = get_renderer('../templates/includes/breadcrumbs.pt').implementation()
    if main:       p['main'] =        get_renderer('../templates/master.pt').implementation()
    if login:
        if not 'came_from' in req.GET:
            req.GET['came_from'] = req.url
        login_params = apex_views.login(req)
        if not isinstance(login_params, HTTPFound):
            login_params['include_came_from'] = True
            login_params['self_register'] = self_registration()
            p['login_params'] = login_params
        else:
            p['login_params'] = {}
        p['login_form'] = get_renderer('apex:templates/apex_template.pt').implementation()
        p['login'] = get_renderer('../templates/includes/login.pt').implementation()
    p['u'] = req.resource_url
    p['root'] = getattr(req, 'root', None)
    p['get_globaltabs'] = get_globaltabs
    p['get_breadcrumbs'] = get_breadcrumbs
    p['static'] = req.static_url('mobyle2.core:static/')[:-1]
    p['dstatic'] = req.static_url('deform:static/')[:-1]
    p['c'] = getattr(req, 'context', None)
    p['request'] = req
    return p

class Base:
    template = None # define in child classes.
    def __init__(self, request):
        self.request = request

    def translate(self, string):
        return auto_translate(self.request, string)

    def __call__(self):
        params = {'view': self}
        params.update(get_base_params(self))
        return render_to_response(self.template, params, self.request)

# vim:set et sts=4 ts=4 tw=0:
