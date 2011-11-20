#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

from sqlalchemy import engine_from_config
from mobyle2.core.models.init import initialize_sql
from mobyle2.core.models.auth import AuthenticationBackend
from mobyle2.core.models import DBSession  as session

def velruse_config(config):
    settings = config.registry.settings
    key = 'velruse.store.'
    if not key+'url' in settings:
        key = 'sqlalchemy.'
    engine = engine_from_config(settings, key)
    providers = settings.get('velruse.providers', '')
    initialize_sql(engine)
    for ab in session.query(AuthenticationBackend).filter(
        AuthenticationBackend.enabled == True
    ):
        t = ab.backend_type
        if ab.backend_type in ['twitter', 'github']:
            providers += '\n%s' % 'velruse.providers.%s' % (t)
            settings['velruse.%s.consumer_key'    % (t)] = ab.username
            settings['velruse.%s.consumer_secret' % (t)] = ab.password
            if ab.authorize:
                if ab.backend_type in ['twitter']:
                    settings['velruse.%s.authorize' %(t)] = ab.authorize
                if ab.backend_type in ['github']:
                    settings['velruse.%s.scope' %(t)] = ab.authorize
    settings['velruse.providers'] = providers

# vim:set et sts=4 ts=4 tw=80:
