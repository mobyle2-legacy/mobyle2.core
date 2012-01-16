#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

import colander, deform

from pyramid.url import resource_url
from pyramid.security import unauthenticated_userid
from pyramid.traversal import resource_path, resource_path_tuple, traverse
from pyramid.renderers import get_renderer
from pyramid.renderers import render_to_response
from pyramid.interfaces import IAuthorizationPolicy
from pyramid.httpexceptions import HTTPFound
from pyramid.threadlocal import get_current_request

from apex import views as apex_views, models as apexmodels

from sqlalchemy.sql import expression as se

from mobyle2.core import validator as v
from mobyle2.core.models import (
    auth as authm,
    user as userm,
    project as projectm,
    DBSession as session,
)
from mobyle2.core.utils import auto_translate, _
from mobyle2.core import widget

from mobyle2.core.basemodel import default_roles


def format_user_for_form(u):
    login = u.login
    username = u.username
    if u.login:
        label = login
    if (not login) and username:
        label = username
    if login and username and (login!=username):
        label += ' %s' % username
    if u.email and (u.email not in label):
        label += '  -- %s' % u.email
    return label


def get_nav_infos(context, request, default_nav_title=''):
    def t(string):
        return auto_translate(request, string)
    i = {}
    i['name'] = t(getattr(context, '__description__', default_nav_title))
    i['url'] = resource_url(context, request)
    i['path'] = resource_path(context)
    return i

def get_breadcrumbs(request, context=None):
    breadcrumbs = []
    req = request
    if not context:
        context = request.context
    pathes = resource_path_tuple(context)
    resources = []
    t = request.root
    for i, item in enumerate(pathes):
        t = traverse(t, item)['context']
        resources.append((i, t, item))
    end = len(resources)
    for i, resource, item in resources:
        infos = get_nav_infos(resource, req, item)
        if i == 0:
            infos['class'] = 'start'
        if 0 < i < end-1:
            infos['class'] = 'middle'
        if i == end-1:
            infos['class'] = 'end'
        breadcrumbs.append(infos)
    return breadcrumbs

def get_globaltabs(request, context=None):
    tabs = []
    r = request.root
    req =request
    if not context:
        context = req.context
    current_path = resource_path(context)
    for item in r.items:
        resource = r[item]
        i = get_nav_infos(resource, req, item)
        i['class'] = ''
        if current_path.startswith(i['path']):
            i['class'] += ' selected'
        tabs.append(i)
    return tabs

def get_base_params(view=None,
                    event=None,
                    request=None,
                    breadcrumbs=True,
                    globaltabs=True,
                    main=True,
                    apex=True,
                    login=True,
                    services_portlet=True,
                    banner=True):
    if event is not None:
        req = event['request']
        view = event['view']
    elif request is not None:
        req = request
    else:
        req = getattr(view, 'request', get_current_request())
    p = {}
    qs = dict(req.GET)
    qs.update(req.POST)
    if apex:
        p['apex_form'] =   get_renderer('apex:templates/forms/tableform.pt').implementation()
        p['apex_template'] =   get_renderer('apex:templates/apex_template.pt').implementation()
    if banner:     p['banner'] =      get_renderer('../templates/includes/banner.pt').implementation()
    if globaltabs: p['globaltabs'] =  get_renderer('../templates/includes/globaltabs.pt').implementation()
    if breadcrumbs:p['breadcrumbs'] = get_renderer('../templates/includes/breadcrumbs.pt').implementation()
    if main:       p['main'] =        get_renderer('../templates/master.pt').implementation()
    ########################### PORTLETS STUFF
    if login:
        if not 'came_from' in req.GET:
            if request is not None:
                userid = unauthenticated_userid(req)
                if not userid:
                    req.GET['came_from'] = req.url
        login_params = apex_views.login(req)
        if not isinstance(login_params, HTTPFound):
            login_params['include_came_from'] = True
            login_params['self_register'] = authm.self_registration()
            p['login_params'] = login_params
        else:
            p['login_params'] = {}
        p['login_form'] = get_renderer('apex:templates/apex_template.pt').implementation()
        p['login'] = get_renderer('../templates/includes/login.pt').implementation()
    if services_portlet:
        p['services'] = get_renderer('../templates/includes/services.pt').implementation()
        p['classifications_service_treeview_url'] = req.resource_url(req.root) + '@@classifications_services_treeview'
        p['packages_service_treeview_url'] = req.resource_url(req.root) + '@@packages_services_treeview'
    p['u'] = req.resource_url
    p['root'] = getattr(req, 'root', None)
    p['get_globaltabs'] = get_globaltabs
    p['services_portlet'] = services_portlet
    p['get_breadcrumbs'] = get_breadcrumbs
    p['static'] = req.static_url('mobyle2.core:static/')[:-1]
    p['dstatic'] = req.static_url('deform:static/')[:-1]
    p['c'] = getattr(req, 'context', None)
    p['request'] = req
    return p

class Base:
    template = None # define in child classes.
    def __init__(self, request):
        self.request = request

    def translate(self, string):
        return auto_translate(self.request, string)

    def get_base_params(self):
        return get_base_params(self)

    @property
    def effective_principals(self):
        ap = self.request.registry.queryUtility(IAuthorizationPolicy)
        global_p = ap.get_contextual_principals(self.request.context)
        return global_p

    def __call__(self):
        params = {'view': self}
        params.update(self.get_base_params())
        return render_to_response(self.template, params, self.request)


class ManageRole(Base):
    template ='../templates/project/project_role.pt'

    def __call__(self):
        form, request, context = None, self.request, self.request.context
        url = "%s@@ajax_users_list" % (
            self.request.resource_url(context)
        )
        gurl = "%s@@ajax_groups_list" % (
            self.request.resource_url(context)
        )
        is_a_get = request.method == 'GET'
        is_a_post = request.method == 'POST'
        params = self.get_base_params()
        rid = -666
        try:
            rid = int(request.params.get('id', '-666'))
        except:
            pass
        p = None
        try:
            p = projectm.Project.by_id(int(rid))
        except Exception, e:
            if isinstance(context, projectm.SecuredObject):
                p = context.context
                rid = p.id
        params['project'] = p
        proxy_roles = context.proxy_roles
        roles = proxy_roles.keys()
        members = {}
        for k in proxy_roles:
            members[k] = {'users': [], 'groups': []}
        if p is not None:
            def reset_default_users_groups(project, members):
                for key in members:
                    data = members[key]
                    for l in data['users'], data['groups']:
                        while len(l) > 0:
                            l.pop()
                    for u in proxy_roles[key].list_users:
                        members[key]['users'].append((u.id,
                                                      format_user_for_form(u.base_user)))
                    for u in proxy_roles[key].list_groups:
                        members[key]['groups'].append((u.id, u.name))
            reset_default_users_groups(context, members)
            class UserS(colander.TupleSchema):
                id = colander.SchemaNode(colander.Int(), missing = '',)
                label = colander.SchemaNode(colander.String(), missing = '',)
            class GroupS(colander.TupleSchema):
                id = colander.SchemaNode(colander.Int(), missing = '',)
                label = colander.SchemaNode(colander.String(), missing = '',)
            class GroupSc(colander.SequenceSchema):
                group = GroupS(name="group", missing=tuple())
            class UserSc(colander.SequenceSchema):
                user = UserS(name="user", missing=tuple())
            def members_factory(name, dmembers):
                dusers, dgroups = dmembers['users'], dmembers['groups']
                class Members(colander.MappingSchema):
                    users = UserSc(name="users", title=_('Users'),widget =
                                   widget.ChosenSelectWidget(url),
                                   default=dusers, validator = v.not_existing_user, missing=tuple(),)
                    groups = GroupSc(name="groups", title=_('Groups'), widget =
                                     widget.ChosenSelectWidget(gurl),
                                     default=dgroups, validator = v.not_existing_group, missing=tuple(),)
                m = Members(name=name, title=default_roles.get(name, name))
                return m
            sh = colander.Schema(title=_('Edit role %s' % p.name),
                   validator=v.role_edit_form_global_validator)
            for r in roles:
                field = members_factory(r, members[r])
                sh.add(field)
            form = widget.Form(request,
                               sh,
                               buttons=(_('Send'),), formid = 'manage_project_roles')
            if is_a_get:
                params['form'] = form.render()
            if is_a_post:
                try:
                    modified = False
                    controls = request.POST.items()
                    fdata  = form.validate(controls)
                    for rolename in proxy_roles:
                        initial_members = members[rolename]
                        data = fdata[rolename]
                        pr = proxy_roles[rolename]
                        users = []
                        for uid, label in data['users']:
                            u = userm.User.by_id(uid)
                            users.append(u)
                        groups = []
                        for uid, label in data['groups']:
                            u = userm.Group.by_id(uid)
                            groups.append(u)
                        for ilist, olist, append, remove in ((users,
                                                              pr.list_users,
                                                              pr.append_user,
                                                              pr.remove_user),
                                                             (groups,
                                                              pr.list_groups,
                                                              pr.append_group,
                                                              pr.remove_group)):
                            if not ilist:
                                modified = True
                                for item in olist[:]:
                                    remove(item)
                            else:
                                for item in ilist:
                                    if not item in olist:
                                        modified = True
                                        append(item)
                                for item in olist[:]:
                                    if not item in ilist:
                                        remove(item)
                                        modified = True
                    if modified:
                        try:
                            session.commit()
                            reset_default_users_groups(p, members)
                            request.session.flash(_('Role modified', 'info'))
                        except Exception, e:
                            try:
                                session.rollback()
                            except:
                                pass
                            request.session.flash(
                                _('Something went wrong'
                                  'while modifying project: %s') % e)
                    params['form'] = form.render()
                except deform.exception.ValidationFailure, e:
                    params['form'] = e.render()
        return render_to_response(self.template, params, request)


class AjaxUsersList(Base):

    def __call__(self):
        term = '%(%)s%(s)s%(%)s' % {
            's': self.request.params.get('term', '').lower(),
            '%': '%',
        }
        table = userm.User
        bu = apexmodels.AuthUser
        rows = session.query(table).join(bu).filter(
            se.and_(
                table.status == 'a',
                se.or_(bu.username.ilike(term),
                       bu.email.ilike(term),
                       bu.login.ilike(term),
                      )
            )
        ).order_by(bu.email, bu.username, bu.login).all()
        data = []
        for row in rows:
            u = row.base_user
            label = format_user_for_form(u)
            item = ("%s"%row.id, label)
            if not item in data:
                data.append(item)
        return data


class AjaxGroupsList(Base):

    def __call__(self):
        term = '%(%)s%(s)s%(%)s' % {
            's': self.request.params.get('term', '').lower(),
            '%': '%',
        }
        table = userm.Group
        rows = session.query(table).filter(
            table.name.ilike(term)
        ).order_by(table.name)
        data = []
        for row in rows:
            label = row.name
            item = ("%s"%row.id, label)
            if not item in data:
                data.append(item)
        return data

# vim:set et sts=4 ts=4 tw=0:
