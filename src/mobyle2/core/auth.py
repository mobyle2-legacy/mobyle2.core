#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import logging

from pyramid.authentication import AuthTktAuthenticationPolicy as BAuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy as BACLAuthorizationPolicy

from mobyle2.core.models import auth, user, project


class AuthTktAuthenticationPolicy(BAuthTktAuthenticationPolicy):
    """Mobyle2 authn policy"""


class ACLAuthorizationPolicy(BACLAuthorizationPolicy):
    """Mobyle2 authz policy"""
    def permits(self, context, principals, permission):
        """map users and groups to their roles !"""
        request = getattr(context, 'request', None)
        try:
            if request:
                ausr = request.user
                if ausr:
                    usr = user.User.by_id(ausr.id)
                    roles = []
                    for r in usr.global_roles:
                        roles.append(r)
                    for ag in request.user.groups:
                        g = user.Group.by_id(ag.id)
                        for r in g.global_roles:
                            if not r in roles:
                                roles.append(r)
                    if isinstance(context, project.Project):
                        for r in usr.project_roles:
                            roles.append(r)
                        for g in user.groups:
                            for r in g.project_roles:
                                if not r in roles:
                                    roles.append(r)
                    for r in roles:
                        rn = r.name
                        if not rn in principals:
                            principals.append(rn) 
                else:
                    # we are not loggued, use anonym mode !
                    principals.append(auth.ANONYME_ROLE)
            else:
                # we are not loggued, use anonym mode !
                principals.append(auth.ANONYME_ROLE)
        except Exception, e:
            logging.getLogger('mobyle2.auth').error(
                'Something went wrong while verifying '
                'user access: %s' % e)

        acl = BACLAuthorizationPolicy.permits(self, context, principals, permission)
        return acl

# vim:set et sts=4 ts=4 tw=80:
