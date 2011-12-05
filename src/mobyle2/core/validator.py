#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

from colander import Invalid

from mobyle2.core.utils import _
from mobyle2.core.models.auth import Role

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

def fail(node, value):
    raise Invalid(node, _('Fail'))


