#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

"""
This module is different from utils.py
as the stuff in there maybe need to import all the application code
it must be imported in last resort.
So, It is separated from utils.py to avoid circular imports.

"""

from apex import models as amodels
from mobyle2.core.models import user, auth, DBSession as session

def create_user(nick, password, superuser=True):
    """."""
    t = [amodels.AuthUser.get_by_login(nick) is None,
          amodels.AuthUser.get_by_username(nick) is None]
    if False in t: raise Exception('%s already exists'%nick)
    usr = amodels.create_user(**{
        'login':nick,
        'username':nick,
        'password':password,
        'email':'%s@mobyle2internal'%nick,
    })
    u = user.User.by_id(usr.id)
    roles, sroles = [], ["internal_user", "external_user"]
    if superuser:
        sroles.append("portal_administrator")
    for r in sroles:
        roles.append(auth.Role.by_name(auth.R[r]))
    for r in roles:
        u.global_roles.append(r)
    session.add(u)
    session.commit()

# vim:set et sts=4 ts=4 tw=80:
