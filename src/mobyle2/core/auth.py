#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

from pyramid.authentication import AuthTktAuthenticationPolicy as BAuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy as BACLAuthorizationPolicy

class AuthTktAuthenticationPolicy(BAuthTktAuthenticationPolicy):
    """Mobyle2 authn policy"""


class ACLAuthorizationPolicy(BACLAuthorizationPolicy):
    """Mobyle2 authz policy"""
    def permits(self, context, principals, permission):
        """map users and groups to their roles !"""
        import pdb;pdb.set_trace()  ## Breakpoint ##
        request = getattr(context, 'request', None)
        roles = []
        BACLAuthorizationPolicy(self, context, principals, permission)

# vim:set et sts=4 ts=4 tw=80:
