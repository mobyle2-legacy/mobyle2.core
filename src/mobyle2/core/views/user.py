#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy

from ordereddict import OrderedDict

from pyramid.renderers import render_to_response
from pyramid.response import Response

from mobyle2.core.models import auth
from mobyle2.core.models import user
from mobyle2.core.models import DBSession as session
from mobyle2.core.models import registry as r
from mobyle2.core.views import Base as bBase, get_base_params as get_base_params
from mobyle2.core import validator as v
from mobyle2.core.utils import _

from deform.exception import ValidationFailure
from pyramid.httpexceptions import HTTPFound
import deform
import colander

from mobyle2.core.events import RegenerateVelruseConfigEvent

from mobyle2.core.models.registry import get_registry_key

bool_values = {
    '1': True,
    '0': False,
    1: True,
    0: False,
    'true': True,
    'false': False,
}

class Base(bBase):
    def get_base_params(self):
        params = {'view': self}
        params.update(get_base_params(self))
        return params

    def __call__(self):
        params = self.get_base_params()
        return render_to_response(self.template, params, self.request)

class Home(Base):
    template ='../templates/user/user_home.pt'

class ManageAcl(Base):
    template ='../templates/user/user_home.pt'

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
                )
            )
            description = colander.SchemaNode(colander.String(), title=_('Role description'),)
        add_form = deform.Form( RoleSH(), buttons=(_('Send'),), formid = 'add_role')
        if is_a_post and deleting:
            items = [a[1] 
                     for a in request.POST.items() 
                     if a[0] == 'delete']
            todelete = session.query(
                auth.Role).filter(
                    auth.Role.id.in_(items)).all()
            noecho = [session.delete(i) for i in todelete]
            session.commit()
            request.session.flash(_('Items have been deleted'))
        if is_a_post and adding:
            controls = request.POST.items()
            try:
                data = add_form.validate(controls)
                role = session.query(
                    auth.Role).filter(
                        auth.Role.name == data['name']
                    ).first()
                if not role:
                    rl = auth.Role(name=data['name'],
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
            auth.Role).order_by(auth.Role.name) .all()
        rdata = []
        for role in roles:
            item = {
                'id': role.id,
                'name': role.name,
                'description':role.description,
            }
            rdata.append(item)
        params['roles'] = rdata
        return render_to_response(self.template, params, request)

# vim:set et sts=4 ts=4 tw=0:
