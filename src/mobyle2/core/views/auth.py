#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy

from ordereddict import OrderedDict

from pyramid.renderers import render_to_response
from pyramid.response import Response

from mobyle2.core.models import auth
from mobyle2.core.models import DBSession as session
from mobyle2.core.models import registry as r
from mobyle2.core.views import Base, get_base_params
from mobyle2.core import validator as v
from mobyle2.core.utils import _

from deform.exception import ValidationFailure
from pyramid.httpexceptions import HTTPFound
import deform
import colander

from mobyle2.core.events import RegenerateVelruseConfigEvent

bool_values = {
    '1': True,
    '0': False,
    1: True,
    0: False,
    'true': True,
    'false': False,
}
class ManageSettings(Base):
    template ='../templates/auth/auth_manage_settings.pt'

    def __call__(self):
        global_auth_settings = [u'auth.allow_anonymous',
                                u'auth.self_registration',
                                u'auth.use_captcha']

        request = self.request
        controls = self.request.POST.items()
        keys = session.query(r.Registry).filter(r.Registry.name.in_(global_auth_settings)).all()
        items = OrderedDict()
        authbackend_schema = colander.SchemaNode(colander.Mapping())
        struct = {}
        for i in keys:
            authbackend_schema.add(
                colander.SchemaNode(colander.Boolean(),
                                    name = i.name.replace('auth.', ''),
                                    default=bool_values.get(i.value.lower(), False)
                                   ))
        form = deform.Form(authbackend_schema, buttons=(_('Send'),), use_ajax=True)
        if request.method == 'POST':
            try:
                struct = form.validate(controls)
                for obj in keys:
                    ki =  obj.name.replace('auth.', '')
                    # store settings in database
                    obj.value = struct.get(ki, False)
                session.commit()
            except  ValidationFailure, e:
                pass
        params = get_base_params(self)
        params['f'] = form.render(struct)
        return render_to_response(self.template, params, self.request)

class List(Base):
    template ='../templates/auth/auth_list.pt'

class Home(Base):
    template ='../templates/auth/auth_home.pt'


class AuthView(Base):
    def __init__(self, request):
        Base.__init__(self, request)
        at = auth.AUTH_BACKENDS.copy()
        existing_types = [a[0]
                          for a in session.query(
                              auth.AuthenticationBackend.backend_type
                          ).filter(
                              auth.AuthenticationBackend.enabled == True
                          ).group_by(
                              auth.AuthenticationBackend.backend_type).all()
                         ]
        for item in copy.deepcopy(at):
            if (item in existing_types) and (item in auth.ONLY_ONE_OF):
                del at[item]
        atv = [('', '')]  + at.items()
        class AuthentSchema(colander.MappingSchema):
            name = colander.SchemaNode(colander.String(), title=_('Name'), validator = v.not_empty_string)
            description = colander.SchemaNode(colander.String(), title=_('Backend description'),)
            enabled = colander.SchemaNode(colander.Boolean(), default = True, title=_('Enabled'), description = _('Is this backend enabled ?'))
            auth_backend = colander.SchemaNode(colander.String(),
                                               widget=deform.widget.SelectWidget(
                                                   **{'values': atv}
                                               ),
                                               validator = colander.OneOf(at.keys()),
                                               title= _('Authentication backend')
                                              )


        class DBSchema(colander.MappingSchema):
            host = colander.SchemaNode(colander.String(), description=_('Host'))
            port = colander.SchemaNode(colander.String(), description=_('Port'))
            password = colander.SchemaNode(colander.String(), description=_('Password'))
            user = colander.SchemaNode(colander.String(), description=_('User'))
            db = colander.SchemaNode(colander.String(), description=_('Database'))

        class LDAPSchema(colander.MappingSchema):
            host = colander.SchemaNode(colander.String(), description=_('Host'))
            port = colander.SchemaNode(colander.String(), description=_('Port'))
            password = colander.SchemaNode(colander.String(), description=_('Password'))
            dn = colander.SchemaNode(colander.String(),
                                     description=_('Base dn mask to connect as in the '
                                                   'form "cn=USERID,ou=people", '
                                                   'ex: "cn=USERID,o=paster,dc=paris,dc=net. '
                                                   'USERID is the placeholder for the login '
                                                   'string the user will input.'))
            # users = colander.SchemaNode(colander.String(), description=_('LDAP filter to grab users'))
            # groups = colander.SchemaNode(colander.String(), description=_('LDAP filter to grab groups'))

        class SimpleOpenidSchema(colander.MappingSchema):
            key = colander.SchemaNode(colander.String(), description=_('API consumer'))
            secret = colander.SchemaNode(colander.String(), description=_('API consumer secret'))

        class SimpleOauthSchema(SimpleOpenidSchema):
            authorize = colander.SchemaNode(colander.String(), description=_('API Scope'), missing=None)

        class FullOauthSchema(SimpleOauthSchema):
            url = colander.SchemaNode(colander.String(), description=_('Service url'), validator = v.not_empty_string)

        class FileSchema(colander.MappingSchema):
            passwd_file = colander.SchemaNode(colander.String(), description=_('Full path to the file'))

        self.sh_map = {'openid': FullOauthSchema,
                       'facebook': SimpleOauthSchema,
                       'twitter':  SimpleOauthSchema,
                       'yahoo': SimpleOpenidSchema,
                       'live': SimpleOauthSchema,
                       'github': SimpleOauthSchema,
                       'google': SimpleOauthSchema,
                       'db': DBSchema,
                       'ldap': LDAPSchema,
                       'file': FileSchema,
                       'base': AuthentSchema,
                      }
        self.fmap = {
            'auth_backend': 'backend_type',
            'enabled': 'enabled',
            'name': 'name',
            'description': 'description',
            'authorize': 'authorize',
            'key' : 'username',
            'secret' : 'password',
            'url': 'url_ba',
            'db': 'database',
            'host': 'hostname',
            'port': 'port',
            'user': 'username',
            'dn': 'ldap_dn',
            'file': 'file',
            'users': 'ldap_users_filter',
            'groups': 'ldap_groups_filter',
        }
        request = self.request
        def global_auth_backend_validator(form, value):
            pass
            #if not value['title'].startswith(value['name']):
            #    exc = colander.Invalid(form, 'Title must start with name')
            #    exc['title'] = 'Must start with name %s' % value['name']
            #    raise exc
        def auth_schema_afterbind(node, kw):
            if kw.get('remove_ab'):
               del node['auth_backend']
        self.sh = self.sh_map['base'](
            validator=global_auth_backend_validator,
            after_bind=auth_schema_afterbind)
        ctx = self.request.context
        # if we are in the context of an auth backend, we cant change the type
        if isinstance(ctx, auth.AuthenticationBackendRessource):
            self.sh = self.sh.bind(remove_ab=True)
        self.for_ajax_form = False
        # maybe we are in an ajax request to solve remaining fields for a particular authtype.
        at = ''
        details_added = False
        if request.method == 'POST':
            at = request.POST.get('load_auth_backend_details')
            if at in auth.AUTH_BACKENDS:
                self.sh['auth_backend'].default = at
                self.for_ajax_form = True
            if not at:
                at = request.POST.get('auth_backend')
            if at in auth.AUTH_BACKENDS:
                details_added = True
                ash = self.sh_map[at](name="auth_backend_infos",
                                      description=_('Authentication backend details'))
                self.sh.add(ash)
        # if we are in the context of an auth backend, filling edit properties
        if isinstance(ctx, auth.AuthenticationBackendRessource):
            ab = ctx.ab
            if not details_added:
                ash = self.sh_map[ab.backend_type](name="auth_backend_infos",
                                      description=_('Authentication backend details'))
                self.sh.add(ash)
            keys = {'name': 'name', 'description':'description', 'backend_type':'auth_backend', 'enabled':'enabled'}
            dkeys = {}
            if (ab.backend_type == at and at != '') or (at == ''):
                if ab.backend_type in ['facebook', 'live', 'yahoo', 'twitter', 'openid', 'google', 'github']:
                    dkeys.update({'username': 'key', 'password':'secret', 'authorize': 'authorize'})
                if ab.backend_type in ['file']:
                    dkeys.update({'file':'file'})
                if ab.backend_type in ['openid']:
                    dkeys.update({'username':'key', 'password':'secret'})
                if ab.backend_type in ['ldap']:
                    dkeys.update({'ldap_groups_filter':'groups', 'ldap_users_filter':'users',
                                  'ldap_dn':'dn', 'hostname':'host', 'port':'port','password':'password'})
                if ab.backend_type in ['db']:
                    dkeys.update({'hostname':'host', 'database':'db','password':'password','port':'port',
                                  'username':'user','password':'password'})
            for k in keys:
                if k in self.sh:
                    self.sh[keys[k]].default = getattr(ab, k)
            for k in dkeys:
                value = getattr(ab, k)
                if value:
                    self.sh['auth_backend_infos'][dkeys[k]].default = value
        self.form = deform.Form(self.sh, buttons=(_('Send'),), formid = 'add_auth_backend')

class Add(AuthView):
    template ='../templates/auth/auth_add.pt'
    def __call__(self):
        #_ = self.translate
        request = self.request
        struct = {}
        params = get_base_params(self)
        form = self.form
        if request.method == 'POST':
            controls = request.POST.items()
            if self.for_ajax_form:
                params['f_content'] = form.render(controls)
            else:
                # we are in regular post, just registering data in database
                try:
                    struct = form.validate(controls)
                    fmap = self.fmap
                    kwargs = {}
                    cstruct = dict([(a, struct[a])
                                    for a in struct if not a =='auth_backend_infos']+
                                   [(a, struct.get('auth_backend_infos', {})[a])
                                    for a in struct.get('auth_backend_infos', {})])
                    for k in cstruct:
                        kwargs[fmap.get(k, k)] = cstruct[k]
                    try:
                        ba = auth.AuthenticationBackend(**kwargs)
                        session.add(ba)
                        self.request.registry.notify(RegenerateVelruseConfigEvent(self.request.registry))
                        session.commit()
                        self.request.session.flash(
                            _('A new authentication backend has been created'),
                            'info')
                        item = self.request.root['auths']["%s"%ba.id]
                        url = request.resource_url(item)
                        return HTTPFound(location=url)
                    except Exception, e:
                        message = _(u'You can try to change some '
                                    'settings because an exception occured '
                                    'while adding your new authbackend '
                                    ': ${msg}',
                                    mapping={'msg': u'%s'%e})
                        self.request.session.flash(message, 'error')
                        session.rollback()
                    # we are set, create the request
                    params['f_content'] = form.render(struct)
                except  ValidationFailure, e:
                    params['f_content'] = e.render()
        if not 'f_content' in params:
            params['f_content'] = form.render()
        if self.for_ajax_form:
            response = Response(params['f_content'])
        else:
            response = render_to_response(self.template, params, self.request)
        return response

class View(AuthView):
    template ='../templates/auth/auth_view.pt'
    def __call__(self):
        params = get_base_params(self)
        params['ab'] = self.request.context.ab
        if not 'f_content' in params:
            params['f_content'] = self.form.render(readonly=True)
        return render_to_response(self.template, params, self.request)

class Edit(AuthView):
    template ='../templates/auth/auth_edit.pt'
    def __call__(self):
        params = get_base_params(self)
        request = self.request
        params['ab'] = ab = self.request.context.ab
        form = self.form
        if request.method == 'POST':
            controls = request.POST.items()
            if self.for_ajax_form:
                params['f_content'] = self.form.render(controls)
            else:
                # we are in regular post, just registering data in database
                try:
                    struct = form.validate(controls)
                    try:
                        fmap = self.fmap
                        kwargs = {}
                        cstruct = dict([(a, struct[a])
                                        for a in struct if not a =='auth_backend_infos']+
                                       [(a, struct.get('auth_backend_infos', {})[a])
                                        for a in struct.get('auth_backend_infos', {})])
                        for k in cstruct:
                            kwargs[fmap.get(k, k)] = cstruct[k]
                        for k in kwargs:
                            setattr(ab, k, kwargs[k])
                        session.add(ab)
                        self.request.registry.notify(RegenerateVelruseConfigEvent(self.request.registry))
                        session.commit()
                        self.request.session.flash(
                            _('Backend has been updated'),
                            'info')
                        item = self.request.root['auths']["%s"%ab.id]
                        url = request.resource_url(item)
                        return HTTPFound(location=url)
                    except Exception, e:
                        message = _(u'You can try to change some '
                                    'settings because an exception occured '
                                    'while adding your new authbackend '
                                    ': ${msg}',
                                    mapping={'msg': u'%s'%e})
                        self.request.session.flash(message, 'error')
                        session.rollback()
                except  ValidationFailure, e:
                    params['f_content'] = e.render()
        if not 'f_content' in params:
            params['f_content'] = self.form.render()
        if self.for_ajax_form:
            response = Response(params['f_content'])
        else:
            response = render_to_response(self.template, params, self.request)
        return response

class Delete(AuthView):
    template ='../templates/auth/auth_delete.pt'
    def __call__(self):
        auths_list = self.request.resource_url(
            self.request.root['auths']
        ) + '@@list'
        class authbackend_delete_schema(colander.MappingSchema):
            submitted = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.HiddenWidget(),
                default='true',
                validator = colander.OneOf(['true']),
                title= _('delete me'))
        params = get_base_params(self)
        request = self.request
        params['ab'] = ab = self.request.context.ab
        form = deform.Form(authbackend_delete_schema(), buttons=(_('Send'),), use_ajax=True)
        params['f_content'] = form.render()
        if request.method == 'POST':
            controls = request.POST.items()
            # we are in regular post, just registering data in database
            try:
                struct = form.validate(controls)
                try:
                    session.delete(ab)
                    self.request.registry.notify(RegenerateVelruseConfigEvent(self.request.registry))
                    session.commit()
                    return HTTPFound(location=auths_list)
                except Exception, e:
                    message = _(u'You can try to change some '
                                'settings because an exception occured '
                                'while adding your new authbackend '
                                ': ${msg}',
                                mapping={'msg': u'%s'%e})
                    self.request.session.flash(message, 'error')
                    session.rollback()
            except  ValidationFailure, e:
                params['f_content'] = e.render()
        response = render_to_response(self.template,
                                      params, self.request)
        return response
# vim:set et sts=4 ts=4 tw=0:
