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


class View(Base):
    template = '../templates/project/project_view.pt'


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
        params = {'view': self}
        params.update(get_base_params(self))
        can_add = False
        can_add = has_permission(P['project_create'], self.request.root, self.request)
        params['can_add'] = can_add
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

# vim:set et sts=4 ts=4 tw=80:
