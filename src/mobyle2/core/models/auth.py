# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import Boolean
from sqlalchemy import ForeignKey
from sqlalchemy import Integer

from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError

from ordereddict import OrderedDict

from mobyle2.core.utils import _
from mobyle2.core.models import Base, DBSession as session
from mobyle2.core.models.registry import get_registry_key 

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

class AuthenticationBackendRessource(object):
    def __init__(self, ab, parent):
        self.ab = ab
        self.__name__ = "%s"%ab.id
        self.__parent__ = parent

class AuthenticationBackends:

    @property
    def items(self):
        return OrderedDict(
            [("%s"%a.id,
              AuthenticationBackendRessource(a, self))
             for a in self.session.query(
                 AuthenticationBackend).all()])

    def __init__(self, name, parent):
        self.__name__ = name
        self.__parent__ = parent
        self.__description__ = _('Authentication backends')
        self.request = parent.request
        self.session = parent.session

    def __getitem__(self, item):
        return self.items.get(item, None)

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

    def __init__(self, id=None, name=None, description=None):
        self.id = id
        self.name = name
        self.description=description

    @classmethod
    def all(cls):
        return session.query(cls).all()

default_permissions = {
   'mobyle2 > view': _('View access'),
   'mobyle2 > delete': _('Delete access'),
   'mobyle2 > edit': _('Edit access'),
   'mobyle2 > create': _('Create access'),
   'mobyle2 > group_create': _('Create group'),
   'mobyle2 > group_delete': _('Delete group'),
   'mobyle2 > group_edit': _('Edit group'),
   'mobyle2 > user_create': _('Create user'),
   'mobyle2 > user_delete': _('Delete user'),
   'mobyle2 > user_edit':   _('Edit user'),
   'mobyle2 > project_view': _('View project'),
   'mobyle2 > project_create': _('Create project'),
   'mobyle2 > project_delete': _('Delete project'),
   'mobyle2 > project_edit':   _('Edit project'),
   'mobyle2 > notebook_view': _('View notebook'),
   'mobyle2 > notebook_create': _('Create notebook'),
   'mobyle2 > notebook_delete': _('Delete notebook'),
   'mobyle2 > notebook_edit':   _('Edit notebook'),
   'mobyle2 > service_view': _('View service'),
   'mobyle2 > service_create': _('Create service'),
   'mobyle2 > service_delete': _('Delete service'),
   'mobyle2 > service_edit':   _('Edit service'),
   'mobyle2 > job_run': _('Run job'),
   'mobyle2 > job_view': _('View job'),
   'mobyle2 > job_create': _('Create job'),
   'mobyle2 > job_delete': _('Delete job'),
   'mobyle2 > job_edit':   _('Edit job'),
}
default_roles = {
    'mobyle2 > anonyme' : _('Anonym'),
    'mobyle2 > internal_user' : _('Internal user'),
    'mobyle2 > external_user' : _('External user'),
    'mobyle2 > project_owner' : _('Project owner'),
    'mobyle2 > project_watcher' : _('Project watcher'),
    'mobyle2 > project_contributor' : _('Project contributor'),
    'mobyle2 > project_manager' : _('Project manager'),
    'mobyle2 > portal_administrator' : _('Portal administrator'),
}


T, F = True, False

default_acls = {
    'mobyle2 > view':             {'mobyle2 > project_watcher' : F, 'mobyle2 > project_contributor' : T,'mobyle2 > anonyme' : T, 'mobyle2 > internal_user' : T, 'mobyle2 > external_user' : T, 'mobyle2 > project_owner' : T, 'mobyle2 > project_manager' : F, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > delete':           {'mobyle2 > project_watcher' : F, 'mobyle2 > project_contributor' : F,'mobyle2 > anonyme' : F, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : F, 'mobyle2 > project_manager' : F, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > edit':             {'mobyle2 > project_watcher' : F, 'mobyle2 > project_contributor' : F,'mobyle2 > anonyme' : F, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : F, 'mobyle2 > project_manager' : F, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > create':           {'mobyle2 > project_watcher' : F, 'mobyle2 > project_contributor' : F,'mobyle2 > anonyme' : F, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : F, 'mobyle2 > project_manager' : F, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > group_create':     {'mobyle2 > project_watcher' : F, 'mobyle2 > project_contributor' : F,'mobyle2 > anonyme' : F, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : F, 'mobyle2 > project_manager' : F, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > group_delete':     {'mobyle2 > project_watcher' : F, 'mobyle2 > project_contributor' : F,'mobyle2 > anonyme' : F, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : F, 'mobyle2 > project_manager' : F, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > group_edit':       {'mobyle2 > project_watcher' : F, 'mobyle2 > project_contributor' : F,'mobyle2 > anonyme' : F, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : F, 'mobyle2 > project_manager' : F, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > user_create':      {'mobyle2 > project_watcher' : F, 'mobyle2 > project_contributor' : F,'mobyle2 > anonyme' : F, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : F, 'mobyle2 > project_manager' : F, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > user_delete':      {'mobyle2 > project_watcher' : F, 'mobyle2 > project_contributor' : F,'mobyle2 > anonyme' : F, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : F, 'mobyle2 > project_manager' : F, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > user_edit':        {'mobyle2 > project_watcher' : F, 'mobyle2 > project_contributor' : F,'mobyle2 > anonyme' : F, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : F, 'mobyle2 > project_manager' : F, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > project_view':     {'mobyle2 > project_watcher' : T, 'mobyle2 > project_contributor' : T,'mobyle2 > anonyme' : T, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : T, 'mobyle2 > project_manager' : T, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > project_create':   {'mobyle2 > project_watcher' : F, 'mobyle2 > project_contributor' : F,'mobyle2 > anonyme' : F, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : T, 'mobyle2 > project_manager' : T, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > project_delete':   {'mobyle2 > project_watcher' : F, 'mobyle2 > project_contributor' : F,'mobyle2 > anonyme' : F, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : T, 'mobyle2 > project_manager' : T, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > project_edit':     {'mobyle2 > project_watcher' : F, 'mobyle2 > project_contributor' : F,'mobyle2 > anonyme' : F, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : T, 'mobyle2 > project_manager' : T, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > notebook_view':    {'mobyle2 > project_watcher' : T, 'mobyle2 > project_contributor' : T,'mobyle2 > anonyme' : T, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : T, 'mobyle2 > project_manager' : T, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > notebook_create':  {'mobyle2 > project_watcher' : F, 'mobyle2 > project_contributor' : T,'mobyle2 > anonyme' : F, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : T, 'mobyle2 > project_manager' : T, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > notebook_delete':  {'mobyle2 > project_watcher' : F, 'mobyle2 > project_contributor' : F,'mobyle2 > anonyme' : F, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : T, 'mobyle2 > project_manager' : T, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > notebook_edit':    {'mobyle2 > project_watcher' : F, 'mobyle2 > project_contributor' : T,'mobyle2 > anonyme' : F, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : T, 'mobyle2 > project_manager' : T, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > service_view':     {'mobyle2 > project_watcher' : T, 'mobyle2 > project_contributor' : T,'mobyle2 > anonyme' : T, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : T, 'mobyle2 > project_manager' : T, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > service_create':   {'mobyle2 > project_watcher' : F, 'mobyle2 > project_contributor' : T,'mobyle2 > anonyme' : F, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : T, 'mobyle2 > project_manager' : T, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > service_delete':   {'mobyle2 > project_watcher' : F, 'mobyle2 > project_contributor' : F,'mobyle2 > anonyme' : F, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : T, 'mobyle2 > project_manager' : T, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > service_edit':     {'mobyle2 > project_watcher' : F, 'mobyle2 > project_contributor' : T,'mobyle2 > anonyme' : F, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : T, 'mobyle2 > project_manager' : T, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > job_run':          {'mobyle2 > project_watcher' : F, 'mobyle2 > project_contributor' : T,'mobyle2 > anonyme' : F, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : T, 'mobyle2 > project_manager' : T, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > job_view':         {'mobyle2 > project_watcher' : T, 'mobyle2 > project_contributor' : T,'mobyle2 > anonyme' : T, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : T, 'mobyle2 > project_manager' : T, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > job_create':       {'mobyle2 > project_watcher' : F, 'mobyle2 > project_contributor' : T,'mobyle2 > anonyme' : F, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : T, 'mobyle2 > project_manager' : T, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > job_delete':       {'mobyle2 > project_watcher' : F, 'mobyle2 > project_contributor' : F,'mobyle2 > anonyme' : F, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : T, 'mobyle2 > project_manager' : T, 'mobyle2 > portal_administrator' : T,}, 
    'mobyle2 > job_edit':         {'mobyle2 > project_watcher' : F, 'mobyle2 > project_contributor' : T,'mobyle2 > anonyme' : F, 'mobyle2 > internal_user' : F, 'mobyle2 > external_user' : F, 'mobyle2 > project_owner' : T, 'mobyle2 > project_manager' : T, 'mobyle2 > portal_administrator' : T,}, 
}
                                      


class UserRole(Base):
    __tablename__ = 'authentication_userrole'
    role_id = Column(Integer, ForeignKey("authentication_role.id", name="fk_userrole_role", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", name="fk_userrole_users", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)


class GroupRole(Base):
    __tablename__ = 'authentication_grouprole'
    role_id = Column(Integer, ForeignKey("authentication_role.id", name="fk_grouprolerole_role", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"),  primary_key=True)
    group_id = Column(Integer, ForeignKey("auth_groups.id", name="fk_grouprole_group", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)


class Role(Base):
    __tablename__ = 'authentication_role'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    description = Column(Unicode(2500))
    global_permissions = relationship(
        "Permission", backref="roles", uselist=True,
        secondary="authentication_acl",
        secondaryjoin="Acl.permission==Permission.id")


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

def register_default_roles(session):
    # authentication settings
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
    session.flush()

def register_default_acls(session):
    # authentication settings
    counter = 0
    for p in default_acls:
        perm = Permission.by_name(p)
        roles = default_acls[p]
        for role in roles:
            access = roles[role]
            orole = Role.by_name(role)
            if access:
                counter +=1
                if not perm in orole.global_permissions:
                    orole.global_permissions.append(perm)
                    session.add(orole)
                    session.commit()
    session.flush()  

