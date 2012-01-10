#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
from copy import deepcopy


from ordereddict import OrderedDict
from mobyle2.core.utils import _

from pyramid.security import (
    authenticated_userid,
    Everyone,
    NO_PERMISSION_REQUIRED,
    Allow,
    Authenticated,
    Deny,
)
from pyramid.decorator import reify

from mobyle2.core.models import DBSession
from mobyle2.core.models import project
from mobyle2.core.models.auth import AuthenticationBackends, Permission, Role, P
from mobyle2.core.models.user import Users, User as U

from pyramid.security import has_permission

from mobyle2.core.basemodel import SecuredObject


mapping_apps = OrderedDict([
    ('projects', project.Projects),
])


class Root(SecuredObject):

    def object_acls(self, acls):
        perms = Permission.all()
        roles = Role.all()
        for perm in perms:
            for role in roles:
                if perm in role.global_permissions:
                    spec = Allow
                else:
                    spec = Deny
                acl = (spec, role.name, perm.name)
                if not acl in acls:
                    self.append_acl(acls, acl)

    def __init__(self, request):
        self.__name__ = ''
        self.__description__ = _('Home')
        self.__parent__ = None
        self.request = request
        self.session = DBSession()
        self.items = OrderedDict()
        maps = deepcopy(mapping_apps)
        SecuredObject.__init__(self)
        is_useradmin = has_permission(P['global_useradmin'], self, request)
        is_authadmin = has_permission(P['global_authadmin'], self, request)
        if is_useradmin:
            maps['auths'] = AuthenticationBackends
        if is_authadmin:
            maps['users'] = Users
        for item in maps:
            self.items[item] = maps[item](item, self)

    def __getitem__(self, item):
        return self.items.get(item, None)

def root_factory(request):
    return Root(request)

# vim:set et sts=4 ts=4 tw=80:
