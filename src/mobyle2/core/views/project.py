#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import copy
import urllib
import logging

from ordereddict import OrderedDict

import pkg_resources

from lxml import etree

from sqlalchemy.sql import expression as se

import colander
from deform.exception import ValidationFailure
import deform

from pyramid.renderers import render_to_response
from pyramid.security import has_permission
from pyramid.httpexceptions import HTTPFound

from mobyle2.core.basemodel import P
from mobyle2.core.views import Base, get_base_params
from mobyle2.core.utils import _
from mobyle2.core import widget
from mobyle2.core.models import (
    project,
    user,
    auth as a,
    DBSession as session
)
from mobyle2.core import validator as v

SERVICE_STYLES_DIR = pkg_resources.resource_filename('mobyle2.core', 'static/service_styles')
R = a.R
J = os.path.join

class CustomResolver(etree.Resolver):
    """CustomResolver is a Resolver for lxml that allows
    (among other things) to handle HTTPS protocol,
    which is not handled natively by lxml/libxml2.
    """
    def resolve(self, url, id, context):
        return self.resolve_file(urllib.urlopen(url), context)

class ProjectView(Base):
    def __init__(self, request):
        Base.__init__(self, request)

        class ProjectSchema(colander.MappingSchema):
            name = colander.SchemaNode(colander.String(),
                                       title=_('Name'),
                                       validator=v.not_empty_string)
            description = colander.SchemaNode(colander.String(),
                                              title=_('Backend description'),)
        self.sh_map = {'base': ProjectSchema}
        self.fmap = {'name': 'name', 'description': 'description'}

        def global_project_validator(form, value):
            pass
        self.sh = self.sh_map['base'](validator=global_project_validator)
        ctx = self.request.context
        if isinstance(ctx, project.ProjectResource):
            ab = ctx.project
            keys = {'name': 'name', 'description': 'description'}
            for k in keys:
                self.sh[keys[k]].default = getattr(ab, k)
        self.form = deform.Form(self.sh, buttons=(_('Send'),),
                                formid='add_project')


class Add(ProjectView):
    template = '../templates/project/project_add.pt'

    def __call__(self):
        #_ = self.translate
        request = self.request
        struct = {}
        params = {}
        params.update(get_base_params(self))
        form = self.form
        if request.method == 'POST':
            controls = request.POST.items()
            # we are in regular post, just registering data in database
            try:
                struct = form.validate(controls)
                fmap = self.fmap
                kwargs = {}
                cstruct = copy.deepcopy(struct)
                for k in cstruct:
                    kwargs[fmap.get(k, k)] = cstruct[k]
                try:
                    kwargs['user'] = user.User.by_id(self.request.user.id)
                    ba = project.Project.create(**kwargs)
                    self.request.session.flash(
                        _('A new project has been created'),
                        'info')
                    item = self.request.root['projects']["%s" % ba.id]
                    url = request.resource_url(item)
                    return HTTPFound(location=url)
                except Exception, e:
                    message = _(u'You can try to change some '
                                'settings because an exception occured '
                                'while adding your new project '
                                ': ${msg}',
                                mapping={'msg': u'%s' % e})
                    self.request.session.flash(message, 'error')
                    session.rollback()
                # we are set, create the request
                params['f_content'] = form.render(struct)
            except  ValidationFailure, e:
                params['f_content'] = e.render()
        if not 'f_content' in params:
            params['f_content'] = form.render()
        return render_to_response(self.template, params, self.request)


class List(Base):
    template = '../templates/project/project_list.pt'
    def __call__(self):
        c = self.request.context
        request = self.request
        params = {}
        params.update(get_base_params(self))
        projects = OrderedDict()
        projects['public'] = {
            'label':_('Public projects') ,
            'items':[c.find_context(project.Project.get_public_project())['item']]}
        def not_present(p):
            ids = []
            for k in projects:
                if p.id in [q.context.id for q in projects[k]['items']]:
                    return False
            return True
        # maybe we are admin and want to see projects from a particular user
        usr, id = None, -666
        anonym = not getattr(self.request, 'user', False)
        if not anonym:
            id = self.request.user.id
        is_project_manager = R['project_manager'] in self.effective_principals
        if 'id' in request.params and is_project_manager:
            try:
                id = int(request.params.get('id'))
                usr = user.User.by_id(id)
            except:
                pass
        if usr is None and not anonym:
            usr = user.User.by_id(self.request.user.id)
        if usr is not None:
            projects['own'] = {'label':_('My projects'), 'items': []}
            pr = project.Project.by_owner(usr)
            for p in pr:
                if not_present(p) and p is not None:
                    projects['own']['items'].append(c.find_context(p)['item'])
            projects['activity'] = {'label':_('Projects where i have activities'), 'items': []}
            pr = project.Project.by_participation(usr)
            for p in pr:
                if not_present(p) and p is not None:
                    projects['activity']['items'].append(c.find_context(p)['item'])
        params['projects_map'] = projects
        return render_to_response(self.template, params, self.request)


class View(Base):
    template = '../templates/project/project_view.pt'
    def __call__(self):
        params = {'view': self}
        params.update(get_base_params(self))
        params['can_edit'] = has_permission(P['project_edit'], self.request.root, self.request)
        params['can_editroles'] = has_permission(P['project_editperm'], self.request.root, self.request)
        return render_to_response(self.template, params, self.request)


class Edit(Add):
    template = '../templates/project/project_add.pt'

    def __call__(self):
        params = {'view': self}
        params.update(get_base_params(self))
        request = self.request
        params['ab'] = ab = self.request.context.project
        form = self.form
        if request.method == 'POST':
            controls = request.POST.items()
            # we are in regular post, just registering data in database
            try:
                struct = form.validate(controls)
                try:
                    fmap = self.fmap
                    kwargs = {}
                    cstruct = copy.deepcopy(struct)
                    for k in cstruct:
                        kwargs[fmap.get(k, k)] = cstruct[k]
                    for k in kwargs:
                        setattr(ab, k, kwargs[k])
                    session.add(ab)
                    session.commit()
                    self.request.session.flash(
                        _('Project has been updated'),
                        'info')
                    item = self.request.root['projects']["%s" % ab.id]
                    url = request.resource_url(item)
                    return HTTPFound(location=url)
                except Exception, e:
                    message = _(u'You can try to change some '
                                'settings because an exception occured '
                                'while editing your authbackend'
                                ': ${msg}',
                                mapping={'msg': u'%s' % e})
                    self.request.session.flash(message, 'error')
                    session.rollback()
            except  ValidationFailure, e:
                params['f_content'] = e.render()
        if not 'f_content' in params:
            params['f_content'] = self.form.render()
        return render_to_response(self.template, params, self.request)


class Home(Add):
    template = '../templates/project/project_home.pt'
    def __call__(self):
        form, request, context = None, self.request, self.request.context
        is_a_get = request.method == 'GET'
        is_a_post = request.method == 'POST'
        params = {'view': self}
        params.update(get_base_params(self))
        can_add = False
        can_add = has_permission(P['project_create'], self.request.root, self.request)
        is_project_manager = R['project_manager'] in self.effective_principals
        url = "%s@@ajax_users_list" % (self.request.resource_url(context))
        if is_project_manager:
            class UserSchema(colander.TupleSchema):
                id = colander.SchemaNode(colander.Int(), missing = '',)
                label = colander.SchemaNode(colander.String(), missing = '',)
            class UserWrap(colander.SequenceSchema):
                user = UserSchema(name="user", missing=tuple())
            class ProjectManagementSchema(colander.MappingSchema):
                userwrap = UserWrap(name="user", title=_("View projects of a member"),
                                    widget = widget.SingleChosenSelectWidget(url, width='400px'),
                                    default=[], validator = v.not_existing_user, missing=tuple(),)
            form = widget.Form(request,
                               ProjectManagementSchema(title=_("Project management")),
                               buttons=(_('Send'),), formid='view_member_projects')
            if is_a_get:
                params['form'] = form.render()
            if is_a_post:
                if is_project_manager:
                    try:
                        modified = False
                        controls = request.POST.items()
                        fdata  = form.validate(controls)
                        id = fdata['userwrap'][0][0]
                        url = "%s@@list?id=%s" % (
                            self.request.resource_url(self.request.context),
                            id
                        )
                        return HTTPFound(location=url)
                        params['form'] = form.render()
                    except deform.exception.ValidationFailure, e:
                        params['form'] = e.render()
        params['can_add'] = can_add
        params['is_project_manager'] = is_project_manager
        return render_to_response(self.template, params, self.request)


class ManageRole(Base):
    template ='../templates/user/user_role.pt'

    def __call__(self):
        params = self.get_base_params()
        form, request = None, self.request
        is_a_post = request.method == 'POST'
        adding = request.params.get('__formid__', '') == 'add_role'
        deleting = request.params.get('role_action', '') == 'delete'
        class RoleSH(colander.MappingSchema):
            name = colander.SchemaNode(
                colander.String(), title=_('Role name'), validator = colander.All(
                    v.not_empty_string,
                    v.existing_role,
                )
            )
            description = colander.SchemaNode(colander.String(), title=_('Role description'),)
        add_form = deform.Form( RoleSH(), buttons=(_('Send'),), formid = 'add_role')
        if is_a_post and deleting:
            items = [a[1]
                     for a in request.POST.items()
                     if a[0] == 'delete']
            todelete = session.query(
                a.Role).filter(
                    se.and_(
                        a.Role.id.in_(items),
                        se.not_(a.Role.name.in_(a.default_roles.keys()))
                    )
                ).all()
            noecho = [session.delete(i) for i in todelete]
            session.commit()
            request.session.flash(_('Items have been deleted'), 'info')
        if is_a_post and adding:
            controls = request.POST.items()
            try:
                data = add_form.validate(controls)
                role = session.query(
                    a.Role).filter(
                        a.Role.name == data['name']
                    ).first()
                if not role:
                    rl = a.Role(name=data['name'],
                                   description=data['description'])
                    session.add(rl)
                    session.commit()
                    request.session.flash(_('Role added: %s' % rl.name, 'info'))
                    params['add_form'] = add_form.render()
            except Exception, e:
                params['add_form'] = e.render()
        else:
            params['add_form'] = add_form.render()
        action = request.params.get('role_action', '')
        roles = session.query(
            a.Role).order_by(a.Role.name).all()
        rdata = []
        for role in roles:
            item = {
                'id': role.id,
                'name': role.name,
                'deletable': not role.name in a.default_roles,
                'description':role.description,
            }
            rdata.append(item)
        params['roles'] = rdata
        return render_to_response(self.template, params, request)

class ServersHome(ProjectView):
    template = '../templates/project/servers_home.pt'
    def __call__(self):
        form, request, context = None, self.request, self.request.context
        is_a_get = request.method == 'GET'
        is_a_post = request.method == 'POST'
        params = {'view': self}
        params.update(get_base_params(self))
        return render_to_response(self.template, params, self.request)

class ServerHome(ServersHome):
    template = '../templates/project/server_home.pt'


class ServicesHome(ServersHome):
    template = '../templates/project/services_home.pt'


class ServiceHome(ServersHome):
    template = '../templates/project/service_home.pt'


class JobCreate(ServersHome):
    template = '../templates/project/job_create.pt'

    def __init__(self, request):
        ServersHome.__init__(self,request)
        c = self.context
        #self.service_pid = '%s%s.%s.%s.pid' % (c.project.name, c.project.id, c.server.name, c.service.name)
        #TODO: service_pid attribute should be revised to (1) ensure service
        # uniqueness on the server and (2) display execution server on the
        # portal
        self.service_pid = '%s.%s' % (c.server.name, c.service.name)
        self.xsl_form_path = J(SERVICE_STYLES_DIR, "form.xsl")
        self.xsl_form_url = 'file://%s' % self.xsl_form_path
        self.xsl_nspath = J(SERVICE_STYLES_DIR, "remove_ns.xsl")
        self.xsl_nsurl =  'file://%s' % self.xsl_nspath
        self.xsl_pipe = [(self.xsl_form_path,
                          {'programPID': "'"+self.service_pid+"'"}), (self.xsl_nspath, {})]
        self.xml_url = c.service.xml_url

    def render_xml_service(self, xml_url=None, xsl_pipe=None):
        if not xml_url: xml_url = self.xml_url
        if not xsl_pipe: xsl_pipe = self.xsl_pipe
        parser = etree.XMLParser(no_network=False)
        parser.resolvers.add(CustomResolver())
        xml = etree.parse(xml_url, parser)
        for uri, params in xsl_pipe:
            xslt_doc = etree.parse(uri, parser)
            transform = etree.XSLT(xslt_doc)
            parser = etree.XMLParser(no_network=False)
            xml = transform(xml, **params)
        return xml

    def __call__(self):
        form, request, context = None, self.request, self.request.context
        form = self.render_xml_service()
        params = {'view': self}
        params.update(get_base_params(self))
        params["form"] = form
        return render_to_response(self.template, params, self.request)


class WorkflowsHome(ServersHome):
    template = '../templates/project/workflows_home.pt'


class ProgramsHome(ServersHome):
    template = '../templates/project/programs_home.pt'


class ViewersHome(ServersHome):
    template = '../templates/project/viewers_home.pt'


class WorkflowHome(ServersHome):
    template = '../templates/project/workflow_home.pt'


class ProgramHome(ServersHome):
    template = '../templates/project/program_home.pt'


class ViewerHome(ServersHome):
    template = '../templates/project/viewer_home.pt'

class Treeview(Base):
    treeview_title = ''
    def __init__(s, request):
        Base.__init__(s, request)
        __ = s.request.translate
        s.items = 0
        s.cache_data = {'servers': {}, 'projects': {}}
        s.tree = s.treeview_node(__(s.treeview_title), state=True)
        s.titles = {
            'services': __('Services'),
            'programs': __('Programs'),
            'workflows': __('Workflows'),
            'viewers': __('Viewers')
        }

    def get_server_resource(self, server, project):
        rproject = self.get_project_resource(project)
        rserver = self.cache_data['servers'].get((server, project), None)
        if rserver is None:
            rserver = self.cache_data['servers'][(server, project)] = rproject.items[
                'servers'].find_context(server)['item']
        return rserver

    def get_project_resource(self, project):
        rproject = self.cache_data['projects'].get(project, None)
        if rproject is None:
            rproject = self.cache_data['projects'][project] = self.request.root.items[
                'projects'].find_context(project)['item']
        return rproject

    def treeview_node(self,
                      name='',
                      attr=None,
                      icon=None,
                      state=False,
                      href='#'):
        if not attr: attr = {}
        self.items += 1
        if not 'id' in attr:
            attr ['id'] = "%s_%s" % (self.treeview_title, self.items)
        if not 'href' in attr:
            attr['href'] = href
        if not icon: icon = 'folder'
        node = {'children': [],
                'state' : state,
                'attr': attr,
                'data' : {'title': name, 'attr': attr, 'icon': icon}}
        if state:
            node['state'] = 'open'
        return node

    def construct_treeview(self):
        """Implement treeview construction here"""

    def __call__(self):
        """A CACHER !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"""
        self.construct_treeview()
        return [self.tree]


class ServicesTreeview(Treeview):
    treeview_title = _('Services')
    by_packages = False
    by_classifications = False

    def fill_treeview(self, data, name='', parent=None):
        request = self.request
        attr = {}
        name = data.get('name', name)
        resource = data.get('resource', None)
        if resource is not None:
            rserver = self.get_server_resource(resource.server, resource.project)
            service = rserver.items[
            '%ss' % resource.type].find_context(resource)['item']
            attr['href'] = '%s@@job_create' % request.resource_url(service)
            name = service.context.name
        subdata = self.treeview_node(name, attr)
        # the first node must be skipped, empty node
        if parent is None:
            parent = self.tree
        else:
            if not subdata["data"]["title"] in [s["data"]["title"] for s in parent['children']]:
                parent['children'].append(subdata)
                parent = subdata
            else:
                parent = [s
                          for s in parent['children']
                          if subdata['data']['title'] == s['data']['title']][0]
        if data.has_key('children'):
            for node_title in data['children']:
                self.fill_treeview(data['children'][node_title],
                                   self.titles.get(node_title, node_title), parent)

    def construct_treeview(self):
        req = self.request
        services = OrderedDict()
        projects = req.root['projects']
        public_project = project.Project.get_public_project()
        rpublic_project = projects.find_context(public_project)['item']
        def add_ressource(rproject):
            if ((not self.by_classifications)
                and (not self.by_packages)):
                raise Exception('by classif or by package!')
            if self.by_packages:
                categs = rproject.context.get_services_by_package()
            elif self.by_classifications:
                categs = rproject.context.get_services_by_classification()
            self.fill_treeview(categs)
        add_ressource(rpublic_project)
        if req.user:
            usr = user.User.by_id(req.user.id)
            for pr in usr.projects:
                rproject = projects.find_context(pr)['item']
                add_ressource(rproject)


class ClassificationsServicesTreeview(ServicesTreeview):
    by_classifications = True


class PackagesServicesTreeview(ServicesTreeview):
    by_packages = True

# vim:set et sts=4 ts=4 tw=80:
