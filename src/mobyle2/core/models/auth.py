from mobyle2.core.models import Base
from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import Integer as Int
from sqlalchemy import Boolean
from sqlalchemy import Integer

from ordereddict import OrderedDict
from mobyle2.core.utils import _

AUTH_BACKENDS =OrderedDict([
	( 'openid'                   , 'openid')   ,
	( 'facebook'                 , 'facebook') ,
	( 'twitter'                  , 'twitter')  ,
	( 'yahoo'                    , 'yahoo')    ,
	( 'live'                     , 'live')     ,
	( 'db'                       , 'db')       ,
	( 'ldap'                     , 'ldap')     ,
	( 'file'                     , 'file')     ,
])


class AuthenticationBackend(Base):
    __tablename__ = 'authentication_backend'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    username = Column(Unicode(50))
    password = Column(Unicode(50))
    port = Column(Int(4))
    url_ba = Column(Unicode(50),)
    backend_type = Column(Unicode(50),)
    enabled = Column(Boolean())
    description = Column(Unicode(255))
    hostname = Column(Unicode(255))
    database = Column(Unicode(255))
    ldap_groups_filter = Column(Unicode(255))
    ldap_users_filter = Column(Unicode(255))
    ldap_dn = Column(Unicode(255))
    description = Column(Unicode(255))
    file = Column(Unicode(255))

    def __init__(self,
                 name=None,
                 username=None,
                 password=None,
                 url_ba=None,
                 database=None,
                 hostname=None,
                 port=None,
                 backend_type=None,
                 enabled=False,
                 description=None,
                 ldap_dn=None,
                 ldap_groups_filter=None,
                 ldap_users_filter=None,
                ):
        self.backend_type = backend_type
        self.database = database
        self.description = description
        self.description = description
        self.enabled = enabled
        self.hostname = hostname
        self.ldap_dn = ldap_dn
        self.ldap_groups_filter = ldap_groups_filter
        self.ldap_users_filter = ldap_users_filter
        self.name = name
        self.password = password
        self.port = port
        self.url_ba = url_ba
        self.username = username

class AuthenticationBackendRessource(object):
    def __init__(self, ab, parent):
        self.ab = ab
        self.__name__ = "%s"%ab.id
        self.__parent__ = parent

class AuthenticationBackends:

    @property
    def items(self):
        return OrderedDict([("%s"%a.id, AuthenticationBackendRessource(a, self))               
                            for a in self.session.query(AuthenticationBackend).all()])         

    def __init__(self, name, parent):
        self.__name__ = name
        self.__parent__ = parent
        self.__description__ = _('Authentication backends')
        self.request = parent.request
        self.session = parent.session

    def __getitem__(self, item):
        return self.items.get(item, None)

