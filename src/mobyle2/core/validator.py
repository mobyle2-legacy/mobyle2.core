#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

from colander import Invalid

from apex.models import AuthUser

from mobyle2.core.utils import _
from mobyle2.core.models.auth import Role
from mobyle2.core.models.user import User, Group
from mobyle2.core.models import DBSession as session

to_be_translated = [
    _('Those roleid do not exists: %s'),
    _('Those userid do not exists: %s'),
    _('This role already exists') ,
    _('This group already exists') , 
    _('Those groupid do not exists: %s'),
    _('This roleid does not exists: %s'),
    _('This userid does not exists: %s'),
    _('This groupid does not exists: %s'),
]
 
def not_empty_string(node, value):
    if not value.strip():
        raise Invalid(node, _('You must set a not null string'))

def existing_validator(node, value, cls, label='item'):
    item, value = None, value.strip()
    try:
        item = session.query(cls).filter(cls.name == value).first()
    except Exception, e:
        raise Invalid(node, _('Unknown Error: %s' % e))
    if item is not None:
        raise Invalid(node, _('This %s already exists'%label))

def not_existing_validator(node, values, table, label='item'):
    if isinstance(values, basestring):
        values = [values]
    errors = []
    for value in values:
        v = value
        if isinstance(v, tuple) or isinstance(v, tuple):
            v = v[0]
        item, v = None, (isinstance(v, int)) and v or v.strip()
        if not v: continue
        try:
            item = session.query(
                table).filter(table.id==int(v)).one()
        except Exception, e:
            pass
        if item is not None:
            continue
        errors.append(v)
    if errors:
        if len(errors) == 1:
            raise Invalid(
                _(node, 'This ${label} does not exists: ${userid}',
                  mapping={'label':label,
                           'userid': '%s'% errors[0]}))
        else:
            raise Invalid(node,
                _('Those ${label} do not exists: ${userids}',
                  mapping={'label':label,
                           'userids': ','.join(['%s'%s for s in errors])}))

def not_existing_role(node, value):
    return not_existing_validator(node, value, Role, 'roleid')

def not_existing_user(node, value):
    return not_existing_validator(node, value, User, 'userid')

def permisiv_not_existing_user(node, value):
    if not value or value in ['-666']:
        return
    return not_existing_validator(node, value, User, 'userid') 

def not_existing_group(node, value):
    return not_existing_validator(node, value, Group, 'groupid')

def existing_group(node, value):
    return existing_validator(node, value, Group, 'group')

def existing_user_validator(node, value, column):
    item, value = None, value.strip()
    try:
        item = session.query(AuthUser).filter(getattr(AuthUser, column) == value).first()
    except Exception, e:
        raise Invalid(node, _('Unknown Error: %s' % e))
    if item is not None:
        raise Invalid(node, _('Already exists'))

def existing_user_username(node, value):
    return existing_user_validator(node, value, 'username')

def existing_user_login(node, value):
    return existing_user_validator(node, value, 'login')

def existing_user_email(node, value):
    return existing_user_validator(node, value, 'email')

def existing_role(node, value):
    return existing_validator(node, value, Role, 'role')  

def group_edit_form_global_validator(form, values):
    validators = [(not_existing_group, values.get('groupid', '')),]
    for v, value in validators:
        v(form, value) 

def user_edit_form_global_validator(form, values):
    pass

def role_edit_form_global_validator(form, values):
    validators = [(not_existing_role, values.get('roleid', '')),]
    for v, value in validators:
        v(form, value)

def fail(node, value):
    raise Invalid(node, _('Fail'))


