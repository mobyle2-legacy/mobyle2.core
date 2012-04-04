#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import logging
from zope.interface import implementer

from pyramid.authentication import (
    AuthTktAuthenticationPolicy as BAuthTktAuthenticationPolicy,
    AuthTktCookieHelper as BAuthTktCookieHelper,
#    text_type,
#    ascii_native_,
    VALID_TOKEN,
)
from pyramid.authorization import (
    ACLAuthorizationPolicy as BACLAuthorizationPolicy,
)

from pyramid.decorator import reify

from pyramid.threadlocal import get_current_request
from pyramid.interfaces import (
    IAuthenticationPolicy,
    IDebugLogger,
    )

from pyramid.security import (
    authenticated_userid,
    Everyone,
    NO_PERMISSION_REQUIRED,
    Allow,
    Authenticated,
    Deny,
)



from mobyle2.models import auth, user, project
from mobyle2.basemodel import R, P, SecuredObject

@implementer(IAuthenticationPolicy)
class AuthTktAuthenticationPolicy(BAuthTktAuthenticationPolicy):
    """Mobyle2 authn policy"""


class ACLAuthorizationPolicy(BACLAuthorizationPolicy):
    """Mobyle2 authz policy"""

    def get_contextual_principals(self, context):
        principals = []
        request = getattr(context, 'request', None)
        if request is None:
            request = get_current_request()
        anonym = True
        try:
            if request:
                ausr = request.user
                if ausr:
                    anonym = False
                    usr = user.User.by_id(ausr.id)
                    roles = []
                    for r in usr.global_roles:
                        roles.append(r)
                    if isinstance(context, SecuredObject):
                        noecho = [roles.append(r)
                                  for r in context.get_roles_for_user(usr)
                                  if not r in roles]
                    for ag in request.user.groups:
                        g = user.Group.by_id(ag.id)
                        for r in g.global_roles:
                            if not r in roles:
                                roles.append(r)
                        if isinstance(context, SecuredObject):
                            noecho = [roles.append(r)
                                      for r in context.get_roles_for_group(g)
                                      if not r in roles]
                    for r in roles:
                        rn = r.name
                        if not rn in principals:
                            principals.append(rn)
            if not anonym:
                #user is at least external
                ext = R['external_user']
                internal = R['internal_user']
                l = ausr.last_login
                if l is not None:
                    if l.external_user:
                        principals.append(ext)
                    if l.internal_user:
                        principals.append(internal)
        except Exception, e:
            raise
            logging.getLogger('mobyle2.auth').error(
                'Something went wrong while verifying '
                'user access: %s' % e)
        # we are not loggued, use anonym mode !
        if anonym:
            principals.append(auth.ANONYMOUS_ROLE)
        if R['portal_administrator'] in principals:
            principals.append(R['project_manager']) 
        return principals


    def permits(self, context, principals, permission):
        """map users and groups to their roles !"""
        for p in self.get_contextual_principals(context):
            if not p in principals:
                principals.append(p)
        acl = BACLAuthorizationPolicy.permits(self, context, principals, permission)
        #if 'ACLDenied' == acl.__class__.__name__:
        #    import pdb;pdb.set_trace()
        return acl


# vim:set et sts=4 ts=4 tw=80:
