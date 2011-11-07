#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'


import os
import pkg_resources
from webob import Request, exc
from pyramid.config import Configurator
from pyramid_beaker import session_factory_from_settings
from mobyle2.core import utils
from pyramid.threadlocal import get_current_registry

from sqlalchemy import engine_from_config

from mobyle2.core.models.init import initialize_sql
from mobyle2.core.config import dn
from mobyle2.core.auth import AuthTktAuthenticationPolicy, ACLAuthorizationPolicy

def get_config(settings, debug=False):
    authentication_policy = AuthTktAuthenticationPolicy(dn)
    authorization_policy = ACLAuthorizationPolicy()
    session_factory = session_factory_from_settings(settings)
    config = Configurator(
        root_factory='%s.models.root.root_factory'%dn,
        authentication_policy=authentication_policy,
        authorization_policy=authorization_policy,
        locale_negotiator=locale_negotiator,
        settings=settings,
    )
    # activate if you want to enable global components
    #  globalreg = getGlobalSiteManager()
    #  config = Configurator(registry=globalreg)
    #  config.setup_registry(settings=settings)
    #  config.include('pyramid_zcml')
    config.begin()
    config.hook_zca()
    if debug:
        config.add_view('%s.views.root.Reload' % dn,     name='reload', context='%s.models.root.Root' % dn)
    for z in settings['zcmls']:
        config.load_zcml(z)
    config.scan('%s.models'%dn)
    config.set_session_factory(session_factory)
    engine = engine_from_config(settings, 'sqlalchemy.')
    initialize_sql(engine)
    config.add_translation_dirs('%s:locale/'%dn)
    config.add_subscriber('%s.subscribers.add_renderer_globals'%dn, 'pyramid.events.BeforeRender')
    config.add_subscriber('%s.subscribers.add_localizer'%dn, 'pyramid.events.NewRequest')
    # static files
    config.add_static_view('s', '%s:static'%dn)
    config.add_static_view('deform', 'deform:static')
    # basr urls
    config.add_view('%s.views.root.Home' % dn,       name='',       context='%s.models.root.Root' % dn)
    # auth managment
    config.add_view('%s.views.auth.Home' % dn,    name='',  context='%s.models.auth.AuthenticationBackends' % dn)
    config.add_view('%s.views.auth.ManageSettings' % dn,    name='manage-settings',  context='%s.models.auth.AuthenticationBackends' % dn)
    config.add_view('%s.views.auth.List' % dn,    name='list',  context='%s.models.auth.AuthenticationBackends' % dn)
    config.add_view('%s.views.auth.Add' % dn,    name='add',  context='%s.models.auth.AuthenticationBackends' % dn)
    #config.add_view('%s.views.auth.Helper' % dn,    name='helper',  context='%s.models.auth.AuthenticationBackends' % dn)
    # project urls
    config.add_view('%s.views.project.List' % dn, name='',     context='%s.models.project.Projects' % dn)
    config.add_view('%s.views.project.Edit' % dn, name='edit', context='%s.models.project.ProjectRessource' % dn)
    config.add_view('%s.views.project.View' % dn, name='',     context='%s.models.project.ProjectRessource' % dn)
    #
    config.end()
    return config

def locale_negotiator(request):
    """This code is inspired by the plonelanguatetool negociation!"""
    settings = get_current_registry().settings
    languages = settings['available_languages'].split()
    # first try from the browser wwanted locales
    browser_pref_langs = request.get('HTTP_ACCEPT_LANGUAGE', '')
    browser_pref_langs = browser_pref_langs.split(',')
    locale_name = ''
    i = 0
    langs = []
    length = len(browser_pref_langs)
    # Parse quality strings and build a tuple like
    # ((float(quality), lang), (float(quality), lang))
    # which is sorted afterwards
    # If no quality string is given then the list order
    # is used as quality indicator
    for lang in browser_pref_langs:
        lang = lang.strip().lower().replace('_', '-')
        if lang:
            l = lang.split(';', 2)
            quality = []
            if len(l) == 2:
                try:
                    q = l[1]
                    if q.startswith('q='):
                        q = q.split('=', 2)[1]
                        quality = float(q)
                except:
                    pass
            if quality == []:
                quality = float(length-i)
            language = l[0]
            if language in languages:
                # If allowed add the language
                langs.append((quality, language))
            else:
                # if we only use simply language codes, we should recognize
                # combined codes as their base code. So 'de-de' is treated
                # as 'de'.
                baselanguage = language.split('-')[0]
                if baselanguage in languages:
                    langs.append((quality, baselanguage))
            i = i + 1
    # Sort and reverse it
    langs.sort()
    langs.reverse()
    # Filter quality string
    langs = map(lambda x: x[1], langs)
    if len(langs):
        locale_name = langs[0]
    # default to the system one
    if not locale_name:
        locale_name = os.environ.get('LANG', 'en')[:2]
    return locale_name

def wsgi_app_factory(global_config, **local_config):
    """
    A paste.httpfactory to wrap a pyramid WSGI based application.
    """
    settings = global_config.copy()
    settings.update(**local_config)
    debug = False
    if global_config.get('debug', 'False').lower() == 'true':
        debug = True
    if debug:
        settings['pyramid.debug_authorization'] = 'true'
        settings['pyramid.debug_notfound'] = 'true'
        settings['pyramid.reload_templates'] = 'true'
    settings['zcmls' ] = utils.splitstrip(settings['zcmls'])
    if not settings['zcmls']:
        settings['zcmls'] = []
    settings['zcmls'].insert(0, 'configure.zcml')
    for i, zcml in enumerate(settings['zcmls']):
        if os.path.sep in zcml:
            zcml = os.path.abspath(zcml)
        else:
            zcml = pkg_resources.resource_filename(dn, zcml)
        settings['zcmls'][i] = zcml
    config = get_config(settings, debug=debug)
    app = config.make_wsgi_app()
    def webbuilder_app(environ, start_response):
        req = Request(environ)
        try:
            resp = req.get_response(app)
            return resp(environ, start_response)
        except Exception, e:
            if not debug:
                return exc.HTTPServerError(str(e))(environ, start_response)
            else:
                raise
    return webbuilder_app

def main():
    return 'implement me'

