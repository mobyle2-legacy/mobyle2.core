#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy

from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound
import deform
import colander
from deform.exception import ValidationFailure

from mobyle2.core.views import Base, get_base_params
from mobyle2.core.utils import _
from mobyle2.core.models import project
from mobyle2.core import validator as v
from mobyle2.core.models import DBSession as session


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
                    kwargs['user'] = self.request.user
                    ba = project.Project(**kwargs)
                    session.add(ba)
                    session.commit()
                    self.request.session.flash(
                        _('A new project has been created'),
                        'info')
                    item = self.request.root['projects']["%s" % ba.id]
                    url = request.resource_url(item)
                    return HTTPFound(location=url)
                except Exception, e:
                    message = _(u'You can try to change some '
                                'settings because an exception occured '
                                'while adding your new authbackend '
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
                                'while adding your new authbackend '
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

# vim:set et sts=4 ts=4 tw=80:
