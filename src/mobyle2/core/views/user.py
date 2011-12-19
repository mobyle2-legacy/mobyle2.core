#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import transaction

from ordereddict import OrderedDict
from colander import Invalid

from pyramid.renderers import render_to_response
from pyramid.response import Response

from sqlalchemy.sql import expression as se
from apex import models as apexmodels

from mobyle2.core.models import auth
from mobyle2.core.models import user
from mobyle2.core.models import DBSession as session
from mobyle2.core.views import Base as bBase, get_base_params as get_base_params
from mobyle2.core import validator as v
from mobyle2.core.utils import _

from deform.exception import ValidationFailure
from pyramid.httpexceptions import HTTPFound
import deform
import colander

from mobyle2.core import widget


bool_values = {
    '1': True,
    '0': False,
    1: True,
    0: False,
    'true': True,
    'false': False,
}

def format_user_for_form(u):
    if u.login:
        label = "%s %s" % (u.login, '%s')
    else:
        label = "%s"
    if (u.login != u.username) or not u.login:
        label = (label % u.username).strip()
    if u.email and (u.email not in label):
        label += '  -- %s' % u.email
    return label

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
        roles = OrderedDict([(str(ro.id), ro)
                             for ro in session.query(auth.Role
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


class ManageUser(Base):
    template ='../templates/user/user_user.pt'
    def __call__(self):
        params = self.get_base_params()
        form, request = None, self.request
        is_a_post = request.method == 'POST'
        deleting = request.params.get('user_action', '') == 'delete'
        if is_a_post and deleting:
            items = [a[1]
                     for a in request.POST.items()
                     if a[0] == 'delete']
            todelete = session.query(
                apexmodels.AuthUser).filter(
                    apexmodels.AuthUser.id.in_(items)
                ).all()
            noecho = [session.delete(i) for i in todelete]
            session.commit()
            request.session.flash(_('Items have been deleted'), 'info')
        action = request.params.get('user_action', '')
        users = session.query(apexmodels.AuthUser).order_by(apexmodels.AuthUser.login,
                                                            apexmodels.AuthUser.username,
                                                            apexmodels.AuthUser.email).all()
        rdata = []
        for u in users:
            item = {
                'id': u.id,
                'username': u.username,
                'login': u.login,
                'email': u.email,
                'deletable': True,
            }
            rdata.append(item)
        params['users'] = rdata
        return render_to_response(self.template, params, request)


class ManageGroup(Base):
    template ='../templates/user/user_group.pt'
    def __call__(self):
        params = self.get_base_params()
        form, request = None, self.request
        is_a_post = request.method == 'POST'
        adding = request.params.get('__formid__', '') == 'add_group'
        default_groups = [a[0]
                          for a in apexmodels.get_default_groups(
                              request.registry.settings)]
        deleting = request.params.get('group_action', '') == 'delete'
        class GroupSH(colander.MappingSchema):
            name = colander.SchemaNode(
                colander.String(),
                title = _('Group name'),
                validator = colander.All(
                    v.not_empty_string,
                    v.existing_group,
                )
            )
            description = colander.SchemaNode(colander.String(), title=_('Group description'),)
        add_form = deform.Form( GroupSH(), buttons=(_('Send'),), formid = 'add_group')
        if is_a_post and deleting:
            items = [a[1]
                     for a in request.POST.items()
                     if a[0] == 'delete' and not a[1] in default_groups]
            todelete = session.query(
                user.Group).filter(
                    se.and_(
                        user.Group.id.in_(items),
                        se.not_(user.Group.name.in_(default_groups))
                    )
                ).all()
            noecho = [session.delete(i) for i in todelete]
            session.commit()
            request.session.flash(_('Items have been deleted'), 'info')
        if is_a_post and adding:
            controls = request.POST.items()
            try:
                data = add_form.validate(controls)
                group = session.query(
                    user.Group).filter(
                        user.Group.name == data['name']
                    ).first()
                if not group:
                    rl = user.Group(name=data['name'], description=data['description'])
                    session.add(rl)
                    session.commit()
                    request.session.flash(_('Group added: %s' % rl.name, 'info'))
                    params['add_form'] = add_form.render()
            except Exception, e:
                params['add_form'] = e.render()
        else:
            params['add_form'] = add_form.render()
        action = request.params.get('group_action', '')
        groups = session.query(
            user.Group).order_by(user.Group.name).all()
        rdata = []
        for group in groups:
            item = {
                'id': group.id,
                'name': group.name,
                'deletable': not group.name in default_groups,
                'description':group.description,
            }
            rdata.append(item)
        params['groups'] = rdata
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

class EditGroup(Base):
    template ='../templates/user/user_editgroup.pt'

    def __call__(self):
        form, request = None, self.request
        url = "%s@@ajax_users_list" % (
            self.request.resource_url(self.request.context)
        )
        is_a_get = request.method == 'GET'
        is_a_post = request.method == 'POST'
        params = self.get_base_params()
        r_types = {'users':_('Users'), 'groups': _('Groups',)}
        rid = -666
        try:
            rid = int(request.params.get('groupid', '-666'))
        except:
            pass
        group = None
        try:
            group = session.query(
                user.Group).filter(user.Group.id==int(rid)).first()
        except:
            pass
        params['group'] = group
        if group is not None:
            group_users = []
            def reset_default_users_groups(group, users,):
                for l in users:
                    while len(l) > 0:
                        l.pop()
                for u in group.users:
                   users.append(
                        (u.id, format_user_for_form(u.base_user))
                    )
            reset_default_users_groups(group, group_users)
            class UserS(colander.TupleSchema):
                id = colander.SchemaNode(colander.Int(), missing = '',)
                label = colander.SchemaNode(colander.String(), missing = '',)
            class UserSc(colander.SequenceSchema):
                user = UserS(name="user", missing=tuple())
            class Members(colander.MappingSchema):
                users = UserSc(name="users", title=_('Users'),widget = widget.ChosenSelectWidget(url), default=group_users, validator = v.not_existing_user, missing=tuple(),)
            class Schema(colander.Schema):
                groupid = colander.SchemaNode(
                    colander.String(),
                    widget = deform.widget.HiddenWidget(),
                    validator = v.not_existing_group,
                    default = rid,
                    name = 'groupid',
                    title = _('Group'),
                )
                name = colander.SchemaNode(
                    colander.String(),
                    widget = deform.widget.TextInputWidget(size=len('%s'%group.name)),
                    default = group.name,
                    name = 'group',
                    title = _('Group'),
                )
                description = colander.SchemaNode(
                    colander.String(),
                    widget = deform.widget.TextAreaWidget(),
                    default = group.description,
                    missing = '',
                    name = 'desc',
                    title = _('Description'),
                )
                members = Members(name="members")
            form = widget.Form(request,
                               Schema(title=_('Edit group'), validator=v.group_edit_form_global_validator),
                               buttons=(_('Send'),), formid = 'add_permission')
            if is_a_get:
                params['form'] = form.render()
            if is_a_post:
                try:
                    modified = False
                    controls = request.POST.items()
                    data  = form.validate(controls)
                    group = user.Group.by_id(data['groupid'])
                    if not group.name == data['name']:
                        group.name = data['name']
                        form.schema['name'].default = group.name
                        modified = True
                    if not group.description == data['description']:
                        group.description = data['description']
                        form.schema['description'].default = group.description
                        modified = True
                    users = []
                    for uid, label in data['members']['users']:
                        u = user.User.by_id(uid)
                        users.append(u)
                    for ilist, olist in ((users, group.users),):
                        if not ilist:
                            modified = True
                            for item in olist[:]:
                                del olist[olist.index(item)]
                        else:
                            for item in ilist:
                                if not item in olist:
                                    modified = True
                                    olist.append(item)
                            for item in olist[:]:
                                if not item in ilist:
                                    del olist[olist.index(item)]
                                    modified = True
                    if modified:
                        session.add(group)
                        try:
                            session.commit()
                            reset_default_users_groups(group, group_users)
                            request.session.flash(_('Group modified', 'info'))
                        except Exception, e:
                            try:
                                session.rollback()
                            except:
                                pass
                            request.session.flash(
                                _('Something went wrong'
                                  'while modifying group: %s') % e)
                    params['form'] = form.render()
                except deform.exception.ValidationFailure, e:
                    params['form'] = e.render()
        return render_to_response(self.template, params, request)

class AddEditUser(Base):
    template ='../templates/user/user_edituser.pt'

    def __call__(self):
        form, request = None, self.request
        gurl = "%s@@ajax_groups_list" % (
            self.request.resource_url(self.request.context)
        )
        is_a_get = request.method == 'GET'
        is_a_post = request.method == 'POST'
        params = self.get_base_params()
        r_types = {'users':_('Users'), 'groups': _('Groups',)}
        rid = -666
        try:
            rid = int(request.params.get('userid', '-666'))
        except:
            pass
        usr = None
        try:
            usr = session.query(
                user.User).filter(
                    user.User.id==int(rid)).first()
        except:
            pass
        def existing_user_validator(node, value, column):
            item, value = None, value.strip()
            try:
                item = session.query(apexmodels.AuthUser).filter(
                    getattr(apexmodels.AuthUser, column) == value).first()
            except Exception, e:
                raise Invalid(node, _('Unknown Error: %s' % e))
            if item is not None:
                if usr.id != item.id:
                    raise Invalid(node, _('Already exists'))
        def existing_user_username(node, value):
            return existing_user_validator(node, value, 'username')

        def existing_user_login(node, value):
            return existing_user_validator(node, value, 'login')

        def existing_user_email(node, value):
            return existing_user_validator(node, value, 'email') 
        default_groups = []
        class GroupS(colander.TupleSchema):
            id = colander.SchemaNode(colander.Int(), missing = '',)
            label = colander.SchemaNode(colander.String(), missing = '',)
        class GroupSc(colander.SequenceSchema):
            group = GroupS(name="group", missing=tuple()) 
        class Groups(colander.MappingSchema):
            groups = GroupSc(name="groups", title=_('Groups'), widget = widget.ChosenSelectWidget(gurl), default=default_groups, validator = v.not_existing_group, missing=tuple(),) 
        class Schema(colander.Schema):
            userid = colander.SchemaNode(
                colander.String(),
                widget = deform.widget.HiddenWidget(),
                validator = v.permisiv_not_existing_user,
                default = rid,
                name = 'userid', title = _('User'),
            )
            name = colander.SchemaNode(
                colander.String(),
                validator = existing_user_login,
                widget = deform.widget.TextInputWidget(size=100),
                name = 'name', title = _('Name'),
            )
            dname = colander.SchemaNode(
                colander.String(),
                validator = existing_user_username,
                widget = deform.widget.TextInputWidget(size=100),
                dname = 'dname', title = _('Display Name'),
            )
            email = colander.SchemaNode(
                colander.String(),
                validator = existing_user_email,
                widget = deform.widget.TextInputWidget(size=100),
                name = 'email', title = _('Email'),
            )
            groups = Groups(name="groups")
        if usr is not None:
            label = _('Edit user')
        else:
            label = _('Add user')
        form = widget.Form(request,
                           Schema(title=label, validator=v.user_edit_form_global_validator),
                           buttons=(_('Send'),), formid = 'add_user') 
        persisted_attrs = {'username':'dname', 
                           'login':'name',  
                           'email': 'email'
                          }
        def fill_form(form, usr, data=None):
            if not data: data = {}
            if usr is not None:
                for attr in persisted_attrs:
                    form_attr = persisted_attrs[attr]
                    dv = None
                    if usr is not None:
                        dv = getattr(usr.base_user, attr, None)
                    default_value = data.get(form_attr, dv)
                    if default_value is not None:
                        form.schema[form_attr].default = default_value
                for l in default_groups:
                    while len(l) > 0:
                        l.pop() 
                if usr is not None:
                    for group in usr.groups:
                        default_groups.append((group.id, group.name)) 
        if is_a_post:
            controls = request.POST.items()
            try:
                data  = form.validate(controls) 
                if usr is not None:
                    modified = False
                    for attr in persisted_attrs:
                        form_attr = persisted_attrs[attr]
                        form_value = data[form_attr]
                        user_value = getattr(usr.base_user, attr)
                        if not user_value == form_value:
                            modified = True
                            setattr(usr.base_user, attr, form_value)
                        groups = []
                        for uid, label in data['groups']['groups']:
                            g = user.Group.by_id(uid)
                            groups.append(g) 
                        for ilist, olist in ((groups, usr.groups),):
                            if not ilist:
                                modified = True
                                for item in olist[:]:
                                    del olist[olist.index(item)]
                            else:
                                for item in ilist:
                                    if not item in olist:
                                        modified = True
                                        olist.append(item)
                                for item in olist[:]:
                                    if not item in ilist:
                                        del olist[olist.index(item)]
                                        modified = True 
                    if modified:
                        try:
                            session.commit()
                            request.session.flash(_('User modified', 'info'))
                        except Exception, e:
                            try:
                                session.rollback()
                            except:
                                pass
                            request.session.flash(
                                _('Something went wrong'
                                  'while modifying user: %s') % e)
                    session.add(usr)
                    fill_form(form, usr, data)
                    params['form'] = form.render()
                elif usr is None and request.params.get('userid', '-666') == '-666':
                    groups = [user.Group.by_id(a[0]) for a in data['groups']['groups']]
                    busr = apexmodels.create_user(**{
                        'email': data['email'],
                        'username': data['name'],
                        'login': data['name'],
                    })
                    usr = user.User.by_id(busr.id)
                    for g in groups:
                        usr.groups.append(g)
                    session.add(usr)
                    session.commit()
                    request.session.flash(_('User was created'), 'info')
                    eurl = self.request.url+'?userid=%s'%usr.id
                    return HTTPFound(eurl)
            except deform.exception.ValidationFailure, e:
                fill_form(form, usr)
                params['form'] = e.render()  
        # get the page
        if is_a_get:
            if usr is not None:
                fill_form(form, usr)
            params['form'] = form.render() 
        return render_to_response(self.template, params, request)

class EditRole(Base):
    template ='../templates/user/user_editrole.pt'

    def __call__(self):
        form, request = None, self.request
        url = "%s@@ajax_users_list" % (
            self.request.resource_url(self.request.context)
        )
        gurl = "%s@@ajax_groups_list" % (
            self.request.resource_url(self.request.context)
        )
        is_a_get = request.method == 'GET'
        is_a_post = request.method == 'POST'
        params = self.get_base_params()
        r_types = {'users':_('Users'), 'groups': _('Groups',)}
        rid = -666
        try:
            rid = int(request.params.get('roleid', '-666'))
        except:
            pass
        role = None
        try:
            role = session.query(
                auth.Role).filter(auth.Role.id==int(rid)).first()
        except:
            pass
        params['role'] = role
        if role is not None:
            role_users = []
            role_groups = []
            def reset_default_users_groups(role, users, groups,):
                for l in users, groups:
                    while len(l) > 0:
                        l.pop()
                for u in role.global_users:
                   users.append(
                        (u.id, format_user_for_form(u.base_user))
                    )
                for group in role.global_groups:
                    groups.append(
                        (group.id, group.name)
                    )
            reset_default_users_groups(role, role_users, role_groups)
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
            class Members(colander.MappingSchema):
                users = UserSc(name="users", title=_('Users'),widget = widget.ChosenSelectWidget(url), default=role_users, validator = v.not_existing_user, missing=tuple(),)
                groups = GroupSc(name="groups", title=_('Groups'), widget = widget.ChosenSelectWidget(gurl), default=role_groups, validator = v.not_existing_group, missing=tuple(),)
            class Schema(colander.Schema):
                roleid = colander.SchemaNode(
                    colander.String(),
                    widget = deform.widget.HiddenWidget(),
                    validator = v.not_existing_role,
                    default = rid,
                    name = 'roleid',
                    title = _('Role'),
                )
                name = colander.SchemaNode(
                    colander.String(),
                    widget = deform.widget.TextInputWidget(size=len('%s'%role.name)),
                    default = role.name,
                    name = 'role',
                    title = _('Role'),
                )
                description = colander.SchemaNode(
                    colander.String(),
                    widget = deform.widget.TextAreaWidget(),
                    default = role.description,
                    missing = '',
                    name = 'desc',
                    title = _('Description'),
                )
                members = Members(name="members")
            form = widget.Form(request,
                               Schema(title=_('Edit role'), validator=v.role_edit_form_global_validator),
                               buttons=(_('Send'),), formid = 'add_permission')
            if is_a_get:
                params['form'] = form.render()
            if is_a_post:
                try:
                    modified = False
                    controls = request.POST.items()
                    data  = form.validate(controls)
                    role = auth.Role.by_id(data['roleid'])
                    if not role.name == data['name']:
                        role.name = data['name']
                        form.schema['name'].default = role.name
                        modified = True
                    if not role.description == data['description']:
                        role.description = data['description']
                        form.schema['description'].default = role.description
                        modified = True
                    users = []
                    for uid, label in data['members']['users']:
                        u = user.User.by_id(uid)
                        users.append(u)
                    groups = []
                    for uid, label in data['members']['groups']:
                        u = user.Group.by_id(uid)
                        groups.append(u)
                    for ilist, olist in ((users, role.global_users), (groups, role.global_groups)):
                        if not ilist:
                            modified = True
                            for item in olist[:]:
                                del olist[olist.index(item)]
                        else:
                            for item in ilist:
                                if not item in olist:
                                    modified = True
                                    olist.append(item)
                            for item in olist[:]:
                                if not item in ilist:
                                    del olist[olist.index(item)]
                                    modified = True
                    if modified:
                        session.add(role)
                        try:
                            session.commit()
                            reset_default_users_groups(role, role_users, role_groups)
                            request.session.flash(_('Role modified', 'info'))
                        except Exception, e:
                            try:
                                session.rollback()
                            except:
                                pass
                            request.session.flash(
                                _('Something went wrong'
                                  'while modifying role: %s') % e)
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
        table = user.User
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
        table = user.Group
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
