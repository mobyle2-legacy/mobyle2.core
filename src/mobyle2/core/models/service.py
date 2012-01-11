# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import Boolean
from sqlalchemy import ForeignKey
from sqlalchemy import Enum
from sqlalchemy import Integer

from sqlalchemy.sql import expression as se

from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy.echema import (
    UniqueConstraint,
    Index,
)

from ordereddict import OrderedDict

from pyramid.decorator import reify


from mobyle2.core.utils import _
from mobyle2.core.models import Base, DBSession as session
from mobyle2.core.models.registry import get_registry_key , set_registry_key
from mobyle2.core.basemodel import (
    default_acls, default_permissions, default_roles,
    R, P, ANONYMOUS_ROLE)


class Service(Base):
    __tablename__ = 'services'
    __table_args__ = (
        UniqueConstraint('name', 'server_id', name='unique_server_service'),
        Index('search_classification', 'classification'),
        Index('search_package', 'package'),
    )
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(100), unique=True)
    server_id = Column(Integer, ForeignKey("servers.id", name="fk_service_server", use_alter=True), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", name="fk_service_project", use_alter=True), nullable=False)
    package = Column(Unicode(2500), default='not read', nullable=False)
    classification = Column(Unicode(2500), default='not read', nullable=False)
    enable = Column(Boolean(), default=True, nullable=False)
    exportable = Column(Boolean(), default=False, nullable=False)
    type = Column(Enum('program', 'workflow', 'viewer', name='service_type'), default='program', nullable=False)

    def __init__(self,
                 name=None,
                 url=None,
                 help_mail=None,
                ):
        self.name = name
        self.url = url
        self.help_mail = help_mail


class ServiceRessource(object):
    def __init__(self, resource, parent):
        self.resource = resource
        self.__name__ = "%s"%resource.id
        self.__parent__ = parent


class Services:

    @property
    def items(self):
        return OrderedDict(
            [("%s"%a.id,
              ServiceRessource(a, self))
             for a in self.session.query(
                 Service).all()])

    def __init__(self, name, parent):
        self.__name__ = name
        self.__parent__ = parent
        self.__description__ = _('Remote Servers')
        self.request = parent.request
        self.session = parent.session

    def __getitem__(self, item):
        return self.items.get(item, None)

