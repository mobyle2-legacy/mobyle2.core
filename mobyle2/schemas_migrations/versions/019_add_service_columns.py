from mobyle2.schemas_migrations import (
    recreate_table_fkeys,
)

from sqlalchemy import *
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Unicode,
    String,
    Enum
)
from copy import deepcopy
import sqlalchemy as s
import migrate  as m
from sqlalchemy.orm import relationship
from migrate.changeset.constraint import ForeignKeyConstraint, PrimaryKeyConstraint

from mobyle2.basemodel import (
    DBSession, MigrateBase as Base, metadata as metadata,
    MDBSession as session,
    R, P, default_permissions, default_roles, default_acls)


def upgrade(migrate_engine):
    """r_meta must be reflected from the current database
    whereas metadata is the current constructed metadata for the migration purpose"""
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    class Acl(Base):
        __tablename__ = 'authentication_acl'
        role = Column(Integer, ForeignKey("authentication_role.id", name="fk_acl_role", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
        permission = Column(Integer, ForeignKey("authentication_permission.id", name="fk_acl_permission", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)


    class Role(Base):
        __tablename__ = 'authentication_role'
        id = Column(Integer, primary_key=True)
        name = Column(Unicode(50), unique=True)
        description = Column(Unicode(2500))
        global_permissions = relationship(
            "Permission", uselist=True,
            secondary="authentication_acl",
            secondaryjoin="Acl.permission==Permission.id")

        def __init__(self, id=None, name=None, description=None, global_permissions=None):
            self.id = id
            self.description = description
            self.name = name
            if global_permissions is not None:
                self.global_permissions.extend(global_permissions)

    class Project(Base):
        __tablename__ = 'projects'
        id = Column(Integer, primary_key=True)
        name = Column(Unicode(50), unique=True)
        description = Column(Unicode(255))
        directory = Column(Unicode(2550))
        user_id = Column(Integer, )

    class Permission(Base):
        __tablename__ = 'authentication_permission'
        id = Column(Integer, primary_key=True)
        name = Column(Unicode(50), unique=True)
        description = Column(Unicode(2500))
        roles = relationship(
            "Role", uselist=True,
            secondary="authentication_acl",
            secondaryjoin="Acl.permission==Role.id")

        def __init__(self, id=None, name=None, description=None, roles=None):
            self.id = id
            self.name = name
            self.description=description
            if roles is not None:
                self.roles.extends(roles)

    class ProjectServer(Base):
        __tablename__ = 'projects_servers'
        project_id = Column(Integer, ForeignKey("servers.id",  name="fk_projectserver_server",  use_alter=True, ondelete="CASCADE", onupdate="CASCADE"),  primary_key=True)
        server_id =  Column(Integer, ForeignKey("projects.id", name="fk_projectserver_project", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"),  primary_key=True)


    class Server(Base):
        __tablename__ = 'servers'
        id = Column(Integer, primary_key=True)
        name = Column(Unicode(50), unique=True)
        url = Column(Unicode(255))
        help_mail = Column(Unicode(255))

        def __init__(self,
                     name=None,
                     url=None,
                     help_mail=None,
                    ):
            self.name = name
            self.url = url
            self.help_mail = help_mail


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
        package = Column(Unicode(2500), default='not read', nullable=False)
        classification = Column(Unicode(2500), default='not read', nullable=False)
        enable = Column(Boolean(), default=True, nullable=False)
        exportable = Column(Boolean(), default=False, nullable=False)
        type = Column(Enum('program', 'workflow', 'viewer', name='service_type'), default='program', nullable=False)
        project_id = Column(Integer, ForeignKey("projects.id", name="fk_service_project", use_alter=True), nullable=False)
        description = Column(Unicode(2500),)

    debug = True
    session.configure(bind=migrate_engine)
    migrate_engine.echo=debug
    metadata.bind = migrate_engine
    """ Create services table """
    r_meta = s.MetaData(migrate_engine, True)
    Base.metadata.bind = migrate_engine

    for o in [Service]:
        t = o.__table__
        if not t.name in r_meta.tables: t.create(migrate_engine)
        r_meta = s.MetaData(migrate_engine, True)
        for c in ['project_id','description']:
            if not c in r_meta.tables[t.name].c: 
                t.c[c].create(table=t)
        recreate_table_fkeys(o, session)
   

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pass

