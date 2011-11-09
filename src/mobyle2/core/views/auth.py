#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
            dn = colander.SchemaNode(colander.String(), description=_('Base dn to connect as'))
            users = colander.SchemaNode(colander.String(), description=_('LDAP filter to grab users'))
            groups = colander.SchemaNode(colander.String(), description=_('LDAP filter to grab groups'))

        class SimpleOauthSchema(colander.MappingSchema):
            key = colander.SchemaNode(colander.String(), description=_('API consumer'))
            secret = colander.SchemaNode(colander.String(), description=_('API consumer secret'))

        class FullOauthSchema(SimpleOauthSchema):
            url = colander.SchemaNode(colander.String(), description=_('Service url'), validator = v.not_empty_string)

        class FileSchema(colander.MappingSchema):
            passwd_file = colander.SchemaNode(colander.String(), description=_('Full path to the file'))

        self.sh_map = {'openid': FullOauthSchema,
                       'facebook': SimpleOauthSchema,
                       'twitter': SimpleOauthSchema,
                       'yahoo': SimpleOauthSchema,
                       'live': SimpleOauthSchema,
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
        self.sh = self.sh_map['base'](validator=global_auth_backend_validator)
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
        ctx = self.request.context
        if isinstance(ctx, auth.AuthenticationBackendRessource):
            ab = ctx.ab
            if not details_added:
                ash = self.sh_map[ab.backend_type](name="auth_backend_infos",
                                      description=_('Authentication backend details'))
                self.sh.add(ash)
            keys = {'name': 'name', 'description':'description', 'backend_type':'auth_backend', 'enabled':'enabled'}
            dkeys = {}
            if (ab.backend_type == at and at != '') or (at == ''):
                if ab.backend_type in ['facebook', 'live', 'yahoo', 'twitter', 'openid']:
                    dkeys.update({'username':'key', 'password':'secret'})
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
                self.sh[keys[k]].default = getattr(ab, k)
            for k in dkeys:
                self.sh['auth_backend_infos'][dkeys[k]].default = getattr(ab, k)
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
    template ='../templates/auth/auth_add.pt'
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
# vim:set et sts=4 ts=4 tw=0:
