#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

from pyramid.url import resource_url
from pyramid.traversal import resource_path, resource_path_tuple, traverse

from pyramid.renderers import get_renderer
from pyramid.renderers import render_to_response

from mobyle2.core.utils import auto_translate

def get_nav_infos(context, request, default_nav_title=''):
    def t(string):
        return auto_translate(request, string)
    _ = t# for babel
    i = {}
    i['name'] = _(getattr(context, '__description__', default_nav_title))
    i['url'] = resource_url(context, request)
    i['path'] = resource_path(context)
    return i

def get_base_params(view,
                    breadcrumbs=True,
                    globaltabs=True,
                    main=True,
                    banner=True):
    req = view.request
    p = {}
    if banner:     p['banner'] =      get_renderer('../templates/includes/banner.pt').implementation()
    if globaltabs: p['globaltabs'] =  get_renderer('../templates/includes/globaltabs.pt').implementation()
    if breadcrumbs:p['breadcrumbs'] = get_renderer('../templates/includes/breadcrumbs.pt').implementation()
    if main:       p['main'] =        get_renderer('../templates/master.pt').implementation()
    p['v'] = view
    p['u'] = req.resource_url
    p['root'] = getattr(req, 'root', None)
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
        params = get_base_params(self)
        return render_to_response(self.template, params, self.request)

    def get_breadcrumbs(self):
        breadcrumbs = []
        req = self.request
        pathes = resource_path_tuple(self.request.context)
        resources = []
        t = self.request.root
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

    def get_globaltabs(self):
        tabs = []
        r = self.request.root
        req = self.request
        current_path = resource_path(req.context)
        for item in r.items:
            resource = r[item]
            i = get_nav_infos(resource, req, item)
            i['class'] = ''
            if current_path.startswith(i['path']):
                i['class'] += ' selected'
            tabs.append(i)
        return tabs

# vim:set et sts=4 ts=4 tw=80:
