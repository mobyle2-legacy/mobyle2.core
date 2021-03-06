#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

import os
#import pkg_resources
from webob import Request, exc
from pyramid.config import Configurator
from pyramid_beaker import session_factory_from_settings
from mobyle2.core import utils
from pyramid.threadlocal import get_current_registry
from pyramid.exceptions import Forbidden

from sqlalchemy import engine_from_config

from mobyle2.core.models import initialize_sql, DBSession
from mobyle2.core.config import dn
from mobyle2.core.auth import AuthTktAuthenticationPolicy, ACLAuthorizationPolicy
from mobyle2.core.models.registry import get_registry_key, set_registry_key

from mobyle2.core.interfaces import IMobyle2View

from mobyle2.core.events import RegenerateVelruseConfigEvent
from pyramid_mailer.interfaces import IMailer

from weberror.evalexception import make_eval_exception

# set the default renderer to use by default mobyle2 templates, then deform templates
from pkg_resources import resource_filename
from deform import Form
deform_templates = resource_filename('deform', 'templates')
mobyle2_templates = resource_filename('mobyle2.core', 'templates/deform')
search_path = (mobyle2_templates,deform_templates)
Form.set_zpt_renderer(search_path)

def locale_negotiator(request):
    """This code is inspired by the plonelanguatetool negociation!"""
    settings = get_current_registry().settings
    languages = settings['available_languages'].split()
    # first try from the browser wwanted locales
    browser_pref_langs = request.environ.get('HTTP_ACCEPT_LANGUAGE', '')
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

def includeme(config, debug=False):
    settings = config.registry.settings
    if len([k.startswith('sqlalchemy.') for k in settings]):
        engine = engine_from_config(settings, 'sqlalchemy.')
        initialize_sql(engine)
    # verify captcha settings
    captcha = get_registry_key('auth.use_captcha', False)
    if captcha:
        settings['apex.use_recaptcha_on_login'] = False
        settings['apex.use_recaptcha_on_forgot'] = False
        settings['apex.use_recaptcha_on_register'] = True
        settings['apex.use_recaptcha_on_reset'] = False
        settings['apex.use_recaptcha_on_useradd'] = False
        rpubk = get_registry_key('auth.recaptcha_public_key', '')
        rprivk =  get_registry_key('auth.recaptcha_private_key', '')
        if rpubk:
            settings['apex.recaptcha_public_key'] = rpubk
        if rprivk:
            settings['apex.recaptcha_private_key'] = rprivk



    projects_dir = settings.get('mobyle2.projects_dir')
    if not projects_dir: raise Exception('please configure mobyle2.projects_dir')
    if not os.path.exists(projects_dir):
        try:
            os.makedirs(projects_dir)
            os.chmod(projects_dir, 0600)
        except Exception, e:
            raise Exception('Cant create directory: %s' % projects_dir)

    config.include('apex', route_prefix='/auth')
    #
    authentication_policy = AuthTktAuthenticationPolicy(dn)
    authorization_policy = ACLAuthorizationPolicy()
    if len([k.startswith('session..') for k in settings]):
        session_factory = session_factory_from_settings(settings)
        config.set_session_factory(session_factory)

    config.set_root_factory('%s.models.root.root_factory'%dn)
    config.set_authorization_policy(authorization_policy)
    config.set_authentication_policy(authentication_policy)
    config.set_locale_negotiator(locale_negotiator)


    mailer = config.registry.queryUtility(IMailer)
    if not mailer:
        config.include('pyramid_mailer')
        mailer = config.registry.queryUtility(IMailer)
    if mailer:
        changed = False
        if 'mail.username' in settings:
            username = settings.get('mail.username')
            if not username:
                del settings['mail.username']
                changed = True
        if 'mail.password' in settings:
            password = settings.get('mail.password')
            if not password:
                del settings['mail.password']
            changed = True
        if changed:
            config.registry.unregisterUtility(mailer, IMailer)
            newmailer = mailer.from_settings(settings)
            config.registry.registerUtility(newmailer, IMailer)

    # activate if you want to enable global components
    #  globalreg = getGlobalSiteManager()
    #  config = Configurator(registry=globalreg)
    #  config.setup_registry(settings=settings)
    #  config.include('pyramid_zcml')
    config.begin()
    config.hook_zca()

    from mobyle2.core.models import auth
    P = auth.P
    #if settings.get('application.debug', False):
    #config.scan('%s.models'%dn)
    # translation directories
    config.add_translation_dirs('%s:locale/'%dn)
    config.add_translation_dirs('deform:locale/')
    config.add_subscriber('%s.subscribers.user_created'%dn, 'apex.events.UserCreatedEvent')
    config.add_subscriber('%s.subscribers.user_deleted'%dn, 'apex.events.UserDeletedEvent')
    config.add_subscriber('%s.subscribers.add_globals'%dn, 'pyramid.events.NewRequest')
    config.add_subscriber('%s.subscribers.regenerate_velruse_config'%dn, '%s.events.RegenerateVelruseConfigEvent' % dn)
    # static files
    config.add_static_view('s', '%s:static'%dn)
    config.add_static_view('deform', 'deform:static')
    config.add_static_view('mobyle2.static', settings['mobyle2.static_dir'])
    # basr urls
    config.add_view('%s.views.root.Home' % dn,    name='',  context='%s.models.root.Root' % dn, permission= P['global_view'])
    #config.add_view('%s.views.root.Pdb' % dn,    name='pdb',  context='%s.models.root.Root' % dn, permission= P['global_view'])
    # auth management
    config.add_view('%s.views.root.Reload' % dn,  name='reload', context='%s.models.root.Root' % dn, permission = P['global_authadmin'])
    config.add_view('%s.views.auth.Home' % dn,    name='',  context='%s.models.auth.AuthenticationBackends' % dn, permission = P['global_authadmin'])
    config.add_view('%s.views.auth.ManageSettings' % dn,    name='manage-settings',  context='%s.models.auth.AuthenticationBackends' % dn, permission = P['global_authadmin'])
    config.add_view('%s.views.auth.List' % dn, name='list', context='%s.models.auth.AuthenticationBackends' % dn, permission = P['global_authadmin'])
    config.add_view('%s.views.auth.Add' % dn,  name='add',  context='%s.models.auth.AuthenticationBackends' % dn, permission = P['global_authadmin'])
    config.add_view('%s.views.auth.View' % dn, name='',     context='%s.models.auth.AuthenticationBackendResource' % dn, permission = P['global_authadmin'])
    config.add_view('%s.views.auth.Edit' % dn, name='edit', context='%s.models.auth.AuthenticationBackendResource' % dn, permission = P['global_authadmin'])
    config.add_view('%s.views.auth.Delete' % dn, name='delete', context='%s.models.auth.AuthenticationBackendResource' % dn, permission = P['global_authadmin'])
    #config.add_view('%s.views.auth.Helper' % dn,    name='helper',  context='%s.models.auth.AuthenticationBackends' % dn)
    # project urls
    config.add_view('%s.views.project.Home' % dn, name='', context='%s.models.project.Projects' % dn, permission = P['global_view'])
    config.add_view('%s.views.project.List' % dn, name='list', context='%s.models.project.Projects' % dn, permission = P['project_list'])
    config.add_view('%s.views.project.Edit' % dn, name='edit', context='%s.models.project.ProjectResource' % dn, permission = P['project_edit'])
    config.add_view('%s.views.project.Add' % dn,  name='add', context='%s.models.project.Projects' % dn, permission = P['project_create'])
    config.add_view('%s.views.project.View' % dn, name='',   context='%s.models.project.ProjectResource' % dn, permission = P['project_view'])
    config.add_view('%s.views.ManageRole' % dn, name='role', context='%s.models.project.ProjectResource' % dn, permission = P['project_editperm'])
    config.add_view('%s.views.AjaxUsersList' % dn, name='ajax_users_list',   context='%s.models.project.ProjectResource' % dn, renderer='json', permission = P['project_editperm'])
    config.add_view('%s.views.AjaxGroupsList' % dn, name='ajax_groups_list', context='%s.models.project.ProjectResource' % dn, renderer='json', permission = P['project_editperm'])
    config.add_view('%s.views.AjaxUsersList' % dn, name='ajax_users_list',   context='%s.models.project.Projects' % dn, renderer='json', permission = P['project_editperm'])
    config.add_view('%s.views.AjaxGroupsList' % dn, name='ajax_groups_list', context='%s.models.project.Projects' % dn, renderer='json', permission = P['project_editperm'])
    config.add_view('%s.views.project.ClassificationsServicesTreeview' % dn, name='classifications_services_treeview', context='%s.models.root.Root' % dn, renderer='json', permission = P['project_list'])
    config.add_view('%s.views.project.ServicesRegistry' % dn, name='services_registry', context='%s.models.root.Root' % dn, renderer='json', permission = P['project_list'])
    config.add_view('%s.views.project.PackagesServicesTreeview' % dn, name='packages_services_treeview', context='%s.models.root.Root' % dn, renderer='json', permission = P['project_list'])
    # project > servers urls
    config.add_view('%s.views.project.ServersHome' % dn, name='', context='%s.models.project.Servers' % dn, permission = P['project_view'])
    config.add_view('%s.views.project.ServerHome' % dn, name='', context='%s.models.project.ServerResource' % dn, permission = P['project_view'])
    config.add_view('%s.views.project.ServicesHome' % dn, name='', context='%s.models.project.Services' % dn, permission = P['project_view'])
    config.add_view('%s.views.project.ServiceHome' % dn, name='', context='%s.models.project.ServiceResource' % dn, permission = P['project_view'])
    config.add_view('%s.views.project.WorkflowsHome' % dn, name='', context='%s.models.project.Workflows' % dn, permission = P['project_view'])
    config.add_view('%s.views.project.ProgramsHome' % dn, name='', context='%s.models.project.Programs' % dn, permission = P['project_view'])
    config.add_view('%s.views.project.ViewersHome' % dn, name='', context='%s.models.project.Viewers' % dn, permission = P['project_view'])
    config.add_view('%s.views.project.WorkflowHome' % dn, name='', context='%s.models.project.WorkflowResource' % dn, permission = P['project_view'])
    config.add_view('%s.views.project.ProgramHome' % dn, name='', context='%s.models.project.ProgramResource' % dn, permission = P['project_view'])
    config.add_view('%s.views.project.JobCreate' % dn, name='job_create', context='%s.models.project.ServiceResource' % dn, permission = P['job_create'])
    config.add_view('%s.views.project.ViewerHome' % dn, name='', context='%s.models.project.ViewerResource' % dn, permission = P['project_view'])
    # users management
    config.add_view('%s.views.user.Home' % dn, name='', context='%s.models.user.Users' % dn, permission = P['global_useradmin'])
    config.add_view('%s.views.user.EditRole' % dn, name='edit_role', context='%s.models.user.Users' % dn, permission = P['global_useradmin'])
    config.add_view('%s.views.user.EditGroup' % dn, name='edit_group', context='%s.models.user.Users' % dn, permission = P['global_useradmin'])
    config.add_view('%s.views.user.AddEditUser' % dn, name='add_user', context='%s.models.user.Users' % dn, permission = P['global_useradmin'])
    config.add_view('%s.views.user.AddEditUser' % dn, name='edit_user', context='%s.models.user.Users' % dn, permission = P['global_useradmin'])
    config.add_view('%s.views.user.ManageAcl' % dn, name='acl', context='%s.models.user.Users' % dn, permission = P['global_useradmin'])
    config.add_view('%s.views.user.ManageRole' % dn, name='role', context='%s.models.user.Users' % dn, permission = P['global_useradmin'])
    config.add_view('%s.views.user.ManageGroup' % dn, name='groups', context='%s.models.user.Users' % dn, permission = P['global_admin'])
    config.add_view('%s.views.user.ManageUser' % dn, name='users', context='%s.models.user.Users' % dn, permission = P['global_admin'])
    config.add_view('%s.views.user.ManagePermission' % dn, name='permission', context='%s.models.user.Users' % dn, permission = P['global_useradmin'])
    config.add_view('%s.views.AjaxUsersList' % dn, name='ajax_users_list', context='%s.models.user.Users' % dn, renderer='json', permission =  P['global_useradmin'])
    config.add_view('%s.views.AjaxGroupsList' % dn, name='ajax_groups_list', context='%s.models.user.Users' % dn, renderer='json', permission = P['global_useradmin'])
    # redirect after login
    config.add_route('redirect_after_login', '/redirect_after_login')
    config.add_view('mobyle2.core.views.root.RedirectAfterLogin', route_name='redirect_after_login', permission = P['global_view'])
    # apex overrides
    render_template = 'mobyle2.core:templates/apex_template.pt'
    config.add_view('mobyle2.core.views.apexviews.login', route_name='apex_login', renderer=render_template, permission = P['global_view'])
    config.add_view('mobyle2.core.views.apexviews.register', route_name='apex_register', renderer=render_template, permission = P['global_view'])
    config.add_view('mobyle2.core.views.apexviews.forgot', route_name='apex_forgot', renderer=render_template, permission = P['global_view'])
    config.add_view('mobyle2.core.views.apexviews.reset', route_name='apex_reset', renderer=render_template, permission = P['global_view'])
    config.add_view('mobyle2.core.views.apexviews.activate', route_name='apex_activate', renderer=render_template, permission = P['global_view'])
    config.add_view('mobyle2.core.views.apexviews.useradd', route_name='apex_useradd', renderer=render_template, permission = P['global_admin'])
    config.add_view('mobyle2.core.views.auth.forbidden', context=Forbidden)
    config.end()
    config.commit()
    from mobyle2.core.models.registry import set_registry_key
    from mobyle2.core.models.project import create_public_workspace
    from mobyle2.core.models.server import create_local_server
    from mobyle2.core.models.project import projects_dir, PROJECTS_DIR
    projects_dir(settings[PROJECTS_DIR])
    create_local_server(registry=config.registry)
    create_public_workspace(registry=config.registry)
    # reflect configuration because we do not have the registry avalaible in the pyramid machinery
    # at the server configuration

    set_registry_key('mobyle2.needrestart', False)
    return config

def wsgi_app_factory(global_config, **local_config):
    """
    A paste.httpfactory to wrap a pyramid WSGI based application.
    """
    settings = global_config.copy()
    settings.update(**local_config)
    debug = False
    if global_config.get('debug', 'False').lower() == 'true':
        settings['application.debug'] = True
    config = Configurator(settings=settings)
    # split configuration in another callable to reuse in tests.
    includeme(config)
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

def weberror_wrapper(app, global_config, **local_config):
    keys = ['error_email', 'from_address', 'show_exceptions',
            'smtp_server', 'smtp_use_tls', 'smtp_username ',
            'smtp_password ', 'error_subject_prefix',]
    for k in keys:
        if k in local_config:
            del local_config[k]
    return make_eval_exception(app, global_config, **local_config)

def main():
    return 'implement me'

