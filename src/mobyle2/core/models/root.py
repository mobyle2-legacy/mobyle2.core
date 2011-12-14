#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
from copy import deepcopy


from ordereddict import OrderedDict
from mobyle2.core.utils import _

from pyramid.security import (
    authenticated_userid,
    Everyone,
    Allow,
    Authenticated,
    Deny,
)
from pyramid.interfaces import IStaticURLInfo
from pyramid.decorator import reify

from mobyle2.core.models import DBSession
from mobyle2.core.models import project
from mobyle2.core.models.auth import AuthenticationBackends, Permission, Role 
from mobyle2.core.models.user import Users, User as U, AuthGroup as G

mapping_apps = OrderedDict([
    ('projects', project.Projects),
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
            maps['users'] = Users
        for item in maps:
            self.items[item] = maps[item](item, self)

    def __getitem__(self, item):
        return self.items.get(item, None)

    @reify
    def __acl__(self):
        request = self.request
        registry = request.registry
        uid = authenticated_userid(self.request)
        static_permission = [(Allow, Everyone, 'view')]
        static_subpaths = [a[2]
                           for a in registry.queryUtility(
                               IStaticURLInfo)._get_registrations(registry)]
        # special case: handle static views
        acls = []
        if request.matched_route:
            if request.matched_route in static_subpaths:
                acls.append(static_permission)
        # otherwise going with business permissions
        else:
            acls = [
                (Allow, Authenticated, 'authenticated'),
            ]
            roles = Role.all()
            perms = Permission.all()
            for perm in perms:
                for role in roles:
                    if perm in role.global_permissions:
                        spec = Allow
                    else:
                        spec = Deny
                    acls.append((spec, role.name, perm.name))
        return acls

def root_factory(request):
    return Root(request)

# vim:set et sts=4 ts=4 tw=80:
