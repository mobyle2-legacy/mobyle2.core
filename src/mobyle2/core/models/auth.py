from mobyle2.core.models import Base
from mobyle2.core.models.registry import get_registry_key
from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import Boolean
from sqlalchemy import ForeignKey
from sqlalchemy import Integer

from sqlalchemy.orm import relationship
from ordereddict import OrderedDict
from mobyle2.core.utils import _

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



class Permisssion(Base):
    __tablename__ = 'authentication_permission'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    description = Column(Unicode(50), nullable=True)

class UserRole(Base):
    __tablename__ = 'authentication_userrole'
    user_id = Column(Integer, ForeignKey("auth_users.id", name="fk_userrole_user", use_alter=True), primary_key=True)
    role_id = Column(Integer, ForeignKey("authentication_role.id", name="fk_userrole_role", use_alter=True), primary_key=True)

class GroupRole(Base):
    __tablename__ = 'authentication_grouprole'
    group_id = Column(Integer, ForeignKey("auth_groups.id", name="fk_grouprole_group", use_alter=True), primary_key=True)
    role_id = Column(Integer, ForeignKey("authentication_role.id", name="fk_grouprolerole_role", use_alter=True),  primary_key=True)

class Role(Base):
    __tablename__ = 'authentication_role'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    description = Column(Unicode(50), unique=True)
    users = relationship("User", backref="roles", uselist=True, 
                         secondary="authentication_userrole", secondaryjoin="UserRole.role_id==Role.id") 


