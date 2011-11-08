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
import deform
import colander

class List(Base):
    template ='auth/auth_list.mako'

class Home(Base):
    template ='auth/auth_home.mako'

bool_values = {
    '1': True,
    '0': False,
    1: True,
    0: False,
    'true': True,
    'false': False,
}
class ManageSettings(Base):
    template ='auth/auth_manage_settings.mako'

    def __call__(self):
        _ = self.request.translate
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
    template ='auth/auth_list.mako'

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

class Add(AuthView):
    template ='../templates/auth/auth_add.pt'
    def __call__(self):
        #_ = self.translate
        request = self.request
        r.register_default_keys(session)
        def global_auth_backend_validator(form, value):
            pass
            #if not value['title'].startswith(value['name']):
            #    exc = colander.Invalid(form, 'Title must start with name')
            #    exc['title'] = 'Must start with name %s' % value['name']
            #    raise exc
        sh = self.sh_map['base'](validator=global_auth_backend_validator)
        params = get_base_params(self)
        struct = {}
        skip_validation = False
        # maybe we are in an ajax request to solve remaining fields for a particular authtype.
        if request.method == 'POST':
            at = request.POST.get('load_auth_backend_details')
            if at in auth.AUTH_BACKENDS:
                sh['auth_backend'].default = at
                skip_validation = True
            if not at:
                at = request.POST.get('auth_backend')
            if at in auth.AUTH_BACKENDS:
                ash = self.sh_map[at](name="auth_backend_infos", 
                                      description=_('Authentication backend details'))
                sh.add(ash)
        form = deform.Form(sh, buttons=(_('Send'),), formid = 'add_auth_backend')
        if request.method == 'POST':
            controls = request.POST.items()
            if skip_validation:
                params['f_content'] = form.render(controls)
            else:
                # we are in regular post, just registering data in database
                try:
                    struct = form.validate(controls)
                    fmap = {
                        'auth_backend': 'backend_type',
                        'enabled': 'enabled',
                        'name': 'name',
                        'description': 'description',
                        'key' : 'username',
                        'secret' : 'password',
                        'url': 'url_ba',
                    }
                    kwargs = {}
                    cstruct = dict([(a, struct[a]) for a in struct if not a =='auth_backend_infos']+
                                   [(a, struct.get('auth_backend_infos', {})[a]) for a in struct.get('auth_backend_infos', {})])
                    for k in cstruct:
                        kwargs[fmap.get(k, k)] = cstruct[k]
                    try:
                        ba = auth.AuthenticationBackend(**kwargs)
                        session.commit()
                    except Exception, e:
                        session.rollback()
                    # we are set, create the request
                    params['f_content'] = form.render(struct)
                except  ValidationFailure, e:
                    params['f_content'] = e.render()
        if not 'f_content' in params:
            params['f_content'] = form.render()
        return render_to_response(self.template, params, self.request)

class AddHelper(Base):
    def __call__(self):
        form = None

# vim:set et sts=4 ts=4 tw=0:
