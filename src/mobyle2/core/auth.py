#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

from pyramid.authentication import AuthTktAuthenticationPolicy as BAuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy as BACLAuthorizationPolicy

class AuthTktAuthenticationPolicy(BAuthTktAuthenticationPolicy):
    pass
class ACLAuthorizationPolicy(BACLAuthorizationPolicy):
    pass 

# vim:set et sts=4 ts=4 tw=80:
