

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
 

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    debug = True
    session.configure(bind=migrate_engine)
    migrate_engine.echo=debug
    metadata.bind = migrate_engine
    real_perms = Permission.all()
    for p in real_perms[:]:
        if not p.name in default_permissions:
            session.delete(p)
            session.commit()
    nreal_perms = [p.name for p in real_perms]
    for p in default_permissions:
        if not p in nreal_perms:
            perm = Permission(name=p, description=default_permissions[p])
            session.add(perm)
            session.commit()
            
    for p in default_acls:
        default_acls
        try:
            perm = Permission.by_name(p)
        except:
            pass
        roles = default_acls[p]
        for role in roles:
            access = roles[role]
            orole = Role.by_name(role)
            if access:
                if not perm in orole.global_permissions:
                    orole.global_permissions.append(perm)
                    session.add(orole)
                    session.commit()
            else:
                if perm in orole.global_permissions:
                    del orole.global_permissions[orole.global_permissions.index(perm)]
                    session.add(orole)
                    session.commit()
    session.flush()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pass  
