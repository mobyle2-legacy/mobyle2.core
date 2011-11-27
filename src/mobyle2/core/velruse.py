#l!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

from sqlalchemy import engine_from_config
from mobyle2.core.models import initialize_sql
from mobyle2.core.models.auth import AuthenticationBackend
from mobyle2.core.models import DBSession  as session
from openid.store import sqlstore

def get_sqlstore(settings):
    table_prefix = 'openid_'
    # Possible side-effect: create a database connection if one isn't
    # already open.
    engine = engine_from_config(settings, 'velruse.store.')
    connection = engine.raw_connection()
    connection.cursor()
    # Create table names to specify for SQL-backed stores.
    tablenames = {
        'associations_table': table_prefix + 'openid_associations',
        'nonces_table': table_prefix + 'openid_nonces',
    }
    types = {
        'postgresql': sqlstore.PostgreSQLStore,
        'postgresql+psycopg2': sqlstore.PostgreSQLStore,
        'mysql': sqlstore.MySQLStore,
        'sqlite3': sqlstore.SQLiteStore,
    }
    url = settings.get('velruse.store.url')
    utype = url.split('://')[0]
    try:
        s = types[utype](connection.connection,
                         **tablenames)
    except KeyError:
        raise Exception(
              "Database engine %s not supported by OpenID library" %
              (settings.DATABASE_ENGINE,)
        )
    try:
        s.createTables()
    except (SystemExit, KeyboardInterrupt, MemoryError), e:
        raise
    except:
        # XXX This is not the Right Way to do this, but because the
        # underlying database implementation might differ in behavior
        # at this point, we can't reliably catch the right
        # exception(s) here. Ideally, the SQL store in the OpenID
        # library would catch exceptions that it expects and fail
        # silently, but that could be bad, too. More ideally, the SQL
        # store would not attempt to create tables it knows already
        # exists.
        pass
    return s

def velruse_config(config):
    settings = config.registry.settings
    settings['velruse.openid.store'] = 'mobyle2.core.velruse.get_sqlstore'
    #settings['velruse.openid.realm'] = settings.get('velruse.openid.realm', 'realm')
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
        if ab.backend_type in ['ldap']:
            providers += '\n%s' % 'velruse.providers.ldapprovider'
            url = 'ldap'
            if ab.use_ssl:
                url += 's'
            url += '://%s' % ab.hostname
            if ab.port:
                url +=':%s' % ab.port
            lk = 'velruse.providers.ldapprovider.urls'
            settings[lk] = settings.get(lk, '')+'\n%s' % url
            settings['velruse.providers.ldapprovider.basedn'] = ab.ldap_dn
        if ab.backend_type in ['openid',]:
            providers += '\n%s' % 'velruse.providers.openidconsumer'
            if ab.realm:
                settings['velruse.openid.realm'] = ab.realm
        if ab.backend_type in ['twitter', 'github', 'google']:
            providers += '\n%s' % 'velruse.providers.%s' % (t)
            settings['velruse.%s.consumer_key'    % (t)] = ab.username
            settings['velruse.%s.consumer_secret' % (t)] = ab.password
            if ab.authorize:
                if ab.backend_type in ['twitter', 'github', 'google']:
                    settings['velruse.%s.authorize' %(t)] = ab.authorize
                if ab.backend_type in ['github']:
                    settings['velruse.%s.scope' %(t)] = ab.authorize
    settings['velruse.providers'] = providers

# vim:set et sts=4 ts=4 tw=80:
