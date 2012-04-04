# -*- coding: utf-8 -*-
import os

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


from mobyle2.utils import _
from mobyle2.models import Base, DBSession as session
from mobyle2.models.registry import get_registry_key , set_registry_key
from mobyle2.basemodel import (
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
    package = Column(Unicode(2500), default=u'not read', nullable=False)
    classification = Column(Unicode(2500), default=u'not read', nullable=False)
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

    @property
    def directory(self):
         directory = None
         if self.id is not None:
             if self.project is not None and self.server is not None:
                 directory = os.path.join(self.project.directory, self.server.name, self.name)
                 if not os.path.exists(directory): os.makedirs(directory)
         if self.id is not None and directory is None:
             raise Exception('service in  inconsistent state, no FS directory')
         return directory

    @property
    def xml_file(self):
        return os.path.join(self.directory, '%s.xml' % (self.name))

    @property
    def xml_url(self):
        return 'file://%s' % self.xml_file
