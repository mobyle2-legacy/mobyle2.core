#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

from colander import Invalid

from mobyle2.core.utils import _

def not_empty_string(node, value):
    if not value.strip():
        raise Invalid(node, _('You must set a not null string'))


