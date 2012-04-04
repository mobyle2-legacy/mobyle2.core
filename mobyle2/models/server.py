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


from mobyle2.utils import _
from mobyle2.models import Base, DBSession as session
from mobyle2.models.registry import get_registry_key , set_registry_key
from mobyle2.basemodel import (
    default_acls, default_permissions, default_roles,
    R, P, ANONYMOUS_ROLE)

LOCAL_SERVER_NAME = 'localhost'

class Server(Base):
    __tablename__ = 'servers'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    url = Column(Unicode(255))
    help_mail = Column(Unicode(255))
    projects = relationship('Project', backref='implied_service', secondary='projects_servers')

    @classmethod
    def get_local_server(self):
        return self.by_name(LOCAL_SERVER_NAME)

    def __init__(self,
                 name=None,
                 url=None,
                 help_mail=None,
                 project=None,
                ):
        self.name = name
        self.url = url
        self.help_mail = help_mail
        self.project = project

class ProjectServer(Base):
    __tablename__ = 'projects_servers'
    project_id = Column(Integer, ForeignKey("projects.id", name="fk_projectserver_project", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"),  primary_key=True)
    server_id =  Column(Integer, ForeignKey("servers.id",  name="fk_projectserver_server", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"),  primary_key=True) 
    project    = relationship('Project')
    server    = relationship('Server')

    def __init__(self, project=None, server=None):
        self.project = project
        self.server = server


def create_local_server(registry=None):
    server_name = LOCAL_SERVER_NAME
    s = None
    try:
        s = Server.by_name(server_name)
    except NoResultFound, e:
        s = Server(name=LOCAL_SERVER_NAME,)
        session.add(s)
        session.commit()


