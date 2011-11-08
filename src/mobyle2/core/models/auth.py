from mobyle2.core.models import Base
from sqlalchemy import Column
from sqlalchemy import Unicode
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
    username = Column(Unicode(50), unique=True)
    password = Column(Unicode(50), unique=True)
    url_ba = Column(Unicode(50), unique=True)
    backend_type = Column(Unicode(50), unique=True)
    enabled = Column(Boolean())
    description = Column(Unicode(255))

    def __init__(self,
                 name='',
                 username='',
                 password='',
                 url_ba='',
                 backend_type='',
                 enabled='',
                 description='',
                ):
        self.name = name
        self.description = description
        self.username = username
        self.password = password
        self.url_ba = url_ba
        self.backend_type = backend_type
        self.enabled = enabled
        self.description = description

class AuthenticationBackendRessource(object):
    def __init__(self, ab, parent):
        self.ab = ab
        self.__name__ = "%s"%ab.id
        self.__parent__ = parent

class AuthenticationBackends:
    def __init__(self, name, parent):
        self.__name__ = name
        self.__parent__ = parent
        self.__description__ = _('Authentication backends')
        self.request = parent.request
        self.session = parent.session
        self.items = OrderedDict([("%s"%a.id, AuthenticationBackendRessource(a, self))
                              for a in self.session.query(AuthenticationBackend).all()])

    def __getitem__(self, item):
        return self.items.get(item, None)

