#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
from ordereddict import OrderedDict
import deform
from deform.exception import ValidationFailure
import colander
from sqlalchemy.sql import expression as se

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

R = a.R

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
        request = self.request

        def global_project_validator(form, value):
            pass
        self.sh = self.sh_map['base'](validator=global_project_validator)
        ctx = self.request.context
        if isinstance(ctx, project.ProjectRessource):
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



# vim:set et sts=4 ts=4 tw=80:
