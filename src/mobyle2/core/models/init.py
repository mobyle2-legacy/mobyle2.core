#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

from mobyle2.core.models import DBSession
from mobyle2.core.models.base import Base
from mobyle2.core.models import registry
from mobyle2.core.models import root
from mobyle2.core.models import project
from mobyle2.core.models import auth

def initialize_sql(engine):
    """Moved from init to avoid circular imports"""
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    registry.register_default_keys(DBSession)

# vim:set et sts=4 ts=4 tw=80:
