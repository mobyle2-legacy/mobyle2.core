#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'


import os
import pkg_resources
from webob import Request, exc
from pyramid.config import Configurator
from mobyle2.core import utils

from sqlalchemy import engine_from_config
from mobyle2.core.models import initialize_sql

from mobyle2.core.config import dn
from mobyle2.core.auth import AuthTktAuthenticationPolicy, ACLAuthorizationPolicy

def wsgi_app_factory(global_config, **local_config):
    """
    A paste.httpfactory to wrap a pyramid WSGI based application.
    """
    settings = global_config.copy()
    settings.update(**local_config)
    authentication_policy = AuthTktAuthenticationPolicy(dn)
    authorization_policy = ACLAuthorizationPolicy()  
    debug = False
    if global_config.get('debug', 'False').lower() == 'true':
        debug = True
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

    config = Configurator(
        #root_factory='birdie.models.RootFactory',
        authentication_policy=authentication_policy,
        authorization_policy=authorization_policy,
        settings=settings
    )
    # activate if you want to enable global components
    #  globalreg = getGlobalSiteManager()
    #  config = Configurator(registry=globalreg)
    #  config.setup_registry(settings=settings)
    #  config.include('pyramid_zcml')

    config.hook_zca()
    for z in settings['zcmls']:
        config.load_zcml(z)
    config.scan('%s.models'%dn) 
    engine = engine_from_config(settings, 'sqlalchemy.')
    initialize_sql(engine)
    config.add_static_view('s', '%s:static'%dn)
    config.add_route('project', '/project/*traverse', factory='%s.models.project.project_factory'%dn)
    config.add_view('%s.views.project.list'%dn, name='list', route_name='project',context='%s.models.project.Projects'%dn)
    config.add_view('%s.views.project.list'%dn, name='', route_name='project',context='%s.models.project.Projects'%dn)
    config.add_view('%s.views.project.view'%dn, name='', route_name='project',context='%s.models.project.ProjectRessource' %dn)
    config.add_view('%s.views.project.edit'%dn, name='edit', route_name='project',context='%s.models.project.ProjectRessource' %dn)
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

