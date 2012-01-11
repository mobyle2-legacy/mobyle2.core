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
from sqlalchemy.orm.exc import NoResultFound

from pyramid.decorator import reify


from mobyle2.core.utils import _
from mobyle2.core.models import Base, DBSession as session
from mobyle2.core.models.registry import get_registry_key , set_registry_key
from mobyle2.core.basemodel import (
    default_acls, default_permissions, default_roles,
    R, P, ANONYMOUS_ROLE)

LOCAL_SERVER_NAME = 'localhost'

class Server(Base):
    __tablename__ = 'servers'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    url = Column(Unicode(255))
    help_mail = Column(Unicode(255))

    @classmethod
    def get_local_server(self):
        return self.by_name(LOCAL_SERVER_NAME)

    def __init__(self,
                 name=None,
                 url=None,
                 help_mail=None,
                ):
        self.name = name
        self.url = url
        self.help_mail = help_mail


class ServerRessource(object):
    def __init__(self, resource, parent):
        self.resource = resource
        self.__name__ = "%s"%resource.id
        self.__parent__ = parent


class Servers:

    @property
    def items(self):
        return OrderedDict(
            [("%s"%a.id,
              ServerRessource(a, self))
             for a in self.session.query(
                 Server).all()])

    def __init__(self, name, parent):
        self.__name__ = name
        self.__parent__ = parent
        self.__description__ = _('Remote Servers')
        self.request = parent.request
        self.session = parent.session

    def __getitem__(self, item):
        return self.items.get(item, None)

def create_local_server(registry=None):
    server_name = LOCAL_SERVER_NAME
    s = None
    try:
        s = Server.by_name(server_name)
    except NoResultFound, e:
        s = Server(name=LOCAL_SERVER_NAME,)
        session.add(s)
        session.commit()


