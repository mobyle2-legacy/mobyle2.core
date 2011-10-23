#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
from mobyle2.core.models import DBSession
from project import Projects

from ordereddict import OrderedDict
mapping_apps = OrderedDict([
    ('projects', Projects),
])
class Root(object):
    def __init__(self, request):
        self.__name__ = ''
        self.__description__ = 'Home'
        self.__parent__ = None
        self.request = request
        self.session = DBSession()
        self.items = {}
        for item in mapping_apps:
            self.items[item] = mapping_apps[item](item, self)

    def __getitem__(self, item):
        return self.items.get(item, None)

def root_factory(request):
    return Root(request)

# vim:set et sts=4 ts=4 tw=80:
