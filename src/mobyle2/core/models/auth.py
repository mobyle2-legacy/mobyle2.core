# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import Boolean
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.sql import expression as se

from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError

from ordereddict import OrderedDict

from pyramid.decorator import reify


from mobyle2.core.utils import _
from mobyle2.core.basemodel import SecuredObject
from mobyle2.core.models import Base, DBSession as session
from mobyle2.core.models.registry import get_registry_key , set_registry_key
from mobyle2.core.basemodel import (
    default_acls, default_permissions, default_roles,
    R, P, ANONYMOUS_ROLE)


AUTH_BACKENDS =OrderedDict([
    ( 'openid'                   , 'openid')   ,
    ( 'facebook'                 , 'facebook') ,
    ( 'twitter'                  , 'twitter')  ,
    ( 'github'                   , 'github')  ,
    ( 'yahoo'                    , 'yahoo')    ,
    ( 'google'                   , 'google')    ,
    ( 'live'                     , 'live')     ,
    ( 'db'                       , 'db')       ,
    ( 'ldap'                     , 'ldap')     ,
    ( 'file'                     , 'file')     ,
])

ONLY_ONE_OF = ['twitter', 'github', 'yahoo',
               'live', 'google', 'openid',]



class AuthenticationBackend(Base):
    __tablename__ = 'authentication_backend'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    username = Column(Unicode(255))
    password = Column(Unicode(255))
    authorize = Column(Unicode(255))
    port = Column(Integer)
    realm = Column(Unicode(255),)
    backend_type = Column(Unicode(50),)
    enabled = Column(Boolean())
    description = Column(Unicode(255))
    hostname = Column(Unicode(255))
    database = Column(Unicode(255))
    use_ssl = Column(Boolean())
    ldap_groups_filter = Column(Unicode(255))
    ldap_users_filter = Column(Unicode(255))
    ldap_dn = Column(Unicode(255))
    description = Column(Unicode(255))
    file = Column(Unicode(255))

    def __init__(self,
                 name=None,
                 username=None,
                 password=None,
                 realm=None,
                 database=None,
                 hostname=None,
                 port=None,
                 backend_type=None,
                 authorize=None,
                 enabled=False,
                 description=None,
                 ldap_dn=None,
                 ldap_groups_filter=None,
                 ldap_users_filter=None,
                 use_ssl=False,
                ):
        self.backend_type = backend_type
        self.database = database
        self.description = description
        self.description = description
        self.enabled = enabled
        self.authorize = authorize
        self.hostname = hostname
        self.ldap_dn = ldap_dn
        self.ldap_groups_filter = ldap_groups_filter
        self.ldap_users_filter = ldap_users_filter
        self.name = name
        self.password = password
        self.port = port
        self.realm = realm
        self.username = username
        self.use_ssl = use_ssl

class AuthenticationBackendResource(SecuredObject):
    def __init__(self, *a, **kw):
        SecuredObject.__init__(self, *a, **kw)
        self.ab = self.context

class AuthenticationBackends(SecuredObject):
    __description__ = _('Authentication backends') 
    _items = None
    @property
    def items(self):
        if not self._items:
            self._items =  OrderedDict(
            [("%s"%a.id,
              AuthenticationBackendResource(a, self, '%s'% a.id))
             for a in self.session.query(
                 AuthenticationBackend).all()]) 
        return self._items


def self_registration():
    return get_registry_key('auth.self_registration')


"""
For each of your business objects, define an ACL container to use in the portal
The form is something like:
class Acl(Base):
     __tablename__ = 'authentication_acl'
     rid =    Column(Integer, ForeignKey("bussiness.id", name="fk_...", use_alter=True), primary_key=True)
     role =   Column(Integer, ForeignKey("authentication_role.id", name="fk_acl_role", use_alter=True), primary_key=True)
     permission = Column(Integer, ForeignKey("authentication_permission.id", name="fk_acl_permission", use_alter=True), primary_key=True)
"""


class Permission(Base):
    __tablename__ = 'authentication_permission'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    description = Column(Unicode(2500))

    def __init__(self, id=None, name=None, description=None, roles=None):
        self.id = id
        self.name = name
        self.description=description
        if roles is not None:
            self.roles.extends(roles)

""""

Perm
1 foo
2 bar

Acl
1 1
1 2

Role
1 car

role = <Role car>
role.global_permissions ==> [<Permission foo>, <Permisssion bar> ]

"""



class Role(Base):
    __tablename__ = 'authentication_role'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    description = Column(Unicode(2500))
    global_permissions = relationship(
        "Permission", backref="roles", uselist=True,
        secondary="authentication_acl",
        secondaryjoin="Acl.permission==Permission.id")

    def __init__(self, id=None, name=None, description=None, global_permissions=None):
        self.id = id
        self.description = description
        self.name = name
        if global_permissions is not None:
            self.global_permissions.extend(global_permissions)


class Acl(Base):
    __tablename__ = 'authentication_acl'
    role = Column(Integer, ForeignKey("authentication_role.id", name="fk_acl_role", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    permission = Column(Integer, ForeignKey("authentication_permission.id", name="fk_acl_permission", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)


def register_default_permissions(session):
    # authentication settings
    for k in default_permissions:
        try:
            session.query(Permission).filter(Permission.name == k).one()
        except NoResultFound, e:
            try:
                session.add(
                    Permission(name=k, description=default_permissions[k])
                )
                session.commit()
            except IntegrityError:
                session.rollback()
    session.flush()

def register_default_roles(session, force=False):
    # authentication settings
    if not force:
        force = not get_registry_key('mobyle2.configured_roles', False)
    if not force:
        return
    for k in default_roles:
        try:
            session.query(Role).filter(Role.name == k).one()
        except NoResultFound, e:
            try:
                session.add(
                    Role(name=k, description=default_roles[k])
                )
                session.commit()
            except IntegrityError:
                session.rollback()
    set_registry_key('mobyle2.configured_roles', "1")
    session.flush()

def register_default_acls(session, force=False):
    # authentication settings
    if not force:
        force = not get_registry_key('mobyle2.configured_acl', False)
    if not force:
        return
    for p in default_acls:
        try:
            perm = Permission.by_name(p)
        except:
            import pdb;pdb.set_trace()  ## Breakpoint ##

        roles = default_acls[p]
        for role in roles:
            access = roles[role]
            orole = Role.by_name(role)
            if access:
                if not perm in orole.global_permissions:
                    orole.global_permissions.append(perm)
                    session.add(orole)
                    session.commit()
            else:
                if perm in orole.global_permissions:
                    del orole.global_permissions[orole.global_permissions.index(perm)]
                    session.add(orole)
                    session.commit()
            set_registry_key('mobyle2.configured_acl', "1")
    session.flush()

