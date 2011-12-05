#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy

from ordereddict import OrderedDict

from pyramid.renderers import render_to_response
from pyramid.response import Response

from sqlalchemy.sql import expression as se

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
from mobyle2.core import widget

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

def construct_schema_acls(request, permissions=None, roles=None):
    if not permissions: permissions = {}
    if not roles: roles = {}
    form_schema = colander.SchemaNode(colander.Mapping())
    roles_schema = widget.TableNode(colander.Mapping(), name='roles')
    append = True
    for i, pid in enumerate(permissions):
        p = permissions[pid]
        perm = widget.TrNode(colander.Mapping(), 
                             name="%s"%p.id, title=p.description)
        for rlid in roles:
            rl = roles[rlid]
            if not rl.description in roles_schema.widget.headers:
                roles_schema.widget.headers.append(_(rl.description))
            role = colander.SchemaNode(
                colander.Boolean(),
                    name = "%s"%rl.id,
                    title = _(rl.description),
                    default=p in rl.global_permissions,
                    missing=None,
                )
            perm.add(role)
        append = False
        roles_schema.add(perm)
    form_schema.add(roles_schema)
    form = deform.Form(form_schema, 
                       buttons=(_('Send'),),
                       use_ajax=True,
                       renderer=widget.renderer_factory(request))
    return form


class ManageAcl(Base):
    template ='../templates/user/user_acl.pt'

    def __call__(self):
        request = self.request
        params = self.get_base_params()
        roles = OrderedDict([(str(r.id), r) 
                             for r in session.query(auth.Role
                                      ).order_by(auth.Role.name).all()])
        permissions = OrderedDict([(str(p.id), p) 
                                   for p in session.query(
                                       auth.Permission
                                   ).order_by(auth.Permission.name).all()])
        data = OrderedDict()
        params['data'] = data
        data['permissions'] = permissions
        data['roles'] = roles
        form = construct_schema_acls(request, permissions=permissions, roles=roles)

        if request.method == 'POST':
            try:
                controls = request.POST.items()
                data = form.validate(controls)
                perms = [permissions.get(pid, None)
                         for pid in data['roles']
                         if permissions.get(pid, None)]
                modified, error = False, False
                try:
                    for permission in perms:
                        mapping = data['roles'][str(permission.id)]
                        rles = [roles.get(rid, None)
                                for rid in mapping
                                if rid in roles]
                        for role in rles:
                            # maybe unactivate role
                            if not mapping[str(role.id)]:
                                if permission in role.global_permissions:
                                    modified = True
                                    role.global_permissions.pop(
                                        role.global_permissions.index(
                                            permission
                                        )
                                    ) 
                                    session.add(role)
                                    session.commit()
                            # maybe activate role
                            else:
                                if not permission in role.global_permissions:
                                    modified = True
                                    role.global_permissions.append(permission)
                                    session.add(role)
                                    session.commit()
                except Exception, e:
                    request.session.flash(_('Something goes wrong while saving access parameters: %s')%e, 'error')
                    error = True
                    # sql failure !
                    try:
                        session.rollback()
                    except:
                        pass
                if modified:
                    if not error:
                        request.session.flash(_('Access parameters have been saved'), 'info')
                    form = construct_schema_acls(request, permissions=permissions, roles=roles)
            except  ValidationFailure, e:
                params['form'] = e.render() 
        if not 'form' in params:
            params['form'] = form.render()
        return render_to_response(self.template, params, request)


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
                    v.existing_group,
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
                    se.and_(
                        auth.Role.id.in_(items),
                        se.not_(auth.Role.name.in_(auth.default_roles.keys()))
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
            auth.Role).order_by(auth.Role.name).all()
        rdata = []
        for role in roles:
            item = {
                'id': role.id,
                'name': role.name,
                'deletable': not role.name in auth.default_roles,
                'description':role.description,
            }
            rdata.append(item)
        params['roles'] = rdata
        return render_to_response(self.template, params, request)

class ManagePermission(Base):
    template ='../templates/user/user_permission.pt'

    def __call__(self):
        params = self.get_base_params()
        form, request = None, self.request
        is_a_post = request.method == 'POST'
        adding = request.params.get('__formid__', '') == 'add_permission'
        deleting = request.params.get('permission_action', '') == 'delete'
        class PermissionSH(colander.MappingSchema):
            name = colander.SchemaNode(
                colander.String(), title=_('Permission name'), validator = colander.All(
                    v.not_empty_string,
                    v.existing_group,
                )
            )
            description = colander.SchemaNode(colander.String(), title=_('Permission description'),)
        add_form = deform.Form( PermissionSH(), buttons=(_('Send'),), formid = 'add_permission')
        if is_a_post and deleting:
            items = [a[1]
                     for a in request.POST.items()
                     if a[0] == 'delete']
            todelete = session.query(
                auth.Permission).filter(
                    se.and_(
                        auth.Permission.id.in_(items),
                        se.not_(auth.Permission.name.in_(auth.default_permissions.keys()))
                    )

                ).all()
            noecho = [session.delete(i) for i in todelete]
            session.commit()
            request.session.flash(_('Items have been deleted'), 'info')
        if is_a_post and adding:
            controls = request.POST.items()
            try:
                data = add_form.validate(controls)
                permission = session.query(
                    auth.Permission).filter(
                        auth.Permission.name == data['name']
                    ).first()
                if not permission:
                    rl = auth.Permission(name=data['name'],
                              description=data['description'])
                    session.add(rl)
                    session.commit()
                    request.session.flash(_('Permission added: %s' % rl.name, 'info'))
                    params['add_form'] = add_form.render()
            except Exception, e:
                params['add_form'] = e.render()
        else:
            params['add_form'] = add_form.render()
        action = request.params.get('permission_action', '')
        permissions = session.query(
            auth.Permission).order_by(auth.Permission.name).all()
        rdata = []
        for permission in permissions:
            item = {
                'id': permission.id,
                'deletable': not permission.name in auth.default_permissions,
                'name': permission.name,
                'description':permission.description,
            }
            rdata.append(item)
        params['permissions'] = rdata
        return render_to_response(self.template, params, request)
# vim:set et sts=4 ts=4 tw=0:
