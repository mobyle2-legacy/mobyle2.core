#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

from colander import Invalid

from mobyle2.core.utils import _
from mobyle2.core.models.auth import Role
from mobyle2.core.models.user import AuthUser, AuthGroup

from mobyle2.core.models import DBSession as session

def not_empty_string(node, value):
    if not value.strip():
        raise Invalid(node, _('You must set a not null string'))

def existing_group(node, value):
    item, value = None, value.strip()
    try:
        item = session.query(Role).filter(Role.name == value).first()
    except Exception, e:
        raise Invalid(node, _('Unknown Error: %s' % e))
    if item is not None:
        raise Invalid(node, _('This role already exists'))

def existing_validator(node, values, table, label='item'):
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

def validate_role(node, value):
    return existing_validator(node, value, Role, 'roleid')
def validate_user(node, value):
    return existing_validator(node, value, AuthUser, 'userid')
def validate_group(node, value):
    return existing_validator(node, value, AuthGroup, 'groupid')

to_be_translated = [
    _('Those roleid do not exists: %s'),
    _('Those userid do not exists: %s'),
    _('Those groupid do not exists: %s'),
    _('This roleid does not exists: %s'),
    _('This userid does not exists: %s'),
    _('This groupid does not exists: %s'),
]

def role_edit_form_global_validator(form, values):
    validators = [(validate_role, values.get('roleid', '')),]
    for v, value in validators:
        v(form, value)

def fail(node, value):
    raise Invalid(node, _('Fail'))


