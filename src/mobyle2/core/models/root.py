#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
from copy import deepcopy
from mobyle2.core.models import DBSession
from project import Projects
from auth import AuthenticationBackends

from ordereddict import OrderedDict
from mobyle2.core.utils import _
mapping_apps = OrderedDict([
    ('projects', Projects),
])
class Root(object):
    def __init__(self, request):
        self.__name__ = ''
        self.__description__ = _('Home')
        self.__parent__ = None
        self.request = request
        self.session = DBSession()
        self.items = OrderedDict()
        maps = deepcopy(mapping_apps)
        is_admin = True # todo : implement
        if is_admin:
            maps['auths'] = AuthenticationBackends
        for item in maps:
            self.items[item] = maps[item](item, self)

    def __getitem__(self, item):
        return self.items.get(item, None)

def root_factory(request):
    return Root(request)

# vim:set et sts=4 ts=4 tw=80:
