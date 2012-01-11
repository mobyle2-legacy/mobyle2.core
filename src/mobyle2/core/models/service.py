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
from sqlalchemy.schema import (
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
    description = Column(Unicode(2500),)
    package = Column(Unicode(2500), default='not read', nullable=False)
    classification = Column(Unicode(2500), default='not read', nullable=False)
    enable = Column(Boolean(), default=True, nullable=False)
    exportable = Column(Boolean(), default=False, nullable=False)
    type = Column(Enum('program', 'workflow', 'viewer', name='service_type'), default='program', nullable=False)
    server = relationship('Server', backref='service')
    project = relationship('Project', backref='service')

    def __init__(self,
                 name = None,
                 package = 'not read',
                 classification = 'not read',
                 enable = True,
                 exportable = True,
                 type = 'program',
                 server=None,
                 project=None,
                ):
        self.name = name
        self.package = package
        self.classification = classification
        self.enable = enable
        self.exportable = exportable
        self.type = type
        self.server = server
        self.project = project

