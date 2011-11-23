#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
from copy import deepcopy
from mobyle2.core.models import DBSession
from mobyle2.core.models import project
from project import Projects
from auth import AuthenticationBackends

from ordereddict import OrderedDict
from mobyle2.core.utils import _

from pyramid.security import Everyone
from pyramid.security import Allow
from pyramid.security import Authenticated

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

    @property
    def __acl__(self):
        acls = [
            (Allow, Everyone, 'view'),
            (Allow, Authenticated, 'authenticated'),
        ]
        return acls

def root_factory(request):
    return Root(request)

# vim:set et sts=4 ts=4 tw=80:
