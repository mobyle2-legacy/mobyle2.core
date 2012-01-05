
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
from migrate import *
from sqlalchemy.orm import relationship

from migrate.changeset.constraint import ForeignKeyConstraint, PrimaryKeyConstraint

from mobyle2.core.basemodel import (
    DBSession, MigrateBase as Base, mmeta as metadata,
    MDBSession as session,
    R, P, default_permissions, default_roles, default_acls)
                             
from sqlalchemy.orm.exc import NoResultFound

class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    description = Column(Unicode(255))
    directory = Column(Unicode(2550))
    user = relationship("User")
    user_id = Column(Integer, ForeignKey("users.id", "fk_project_user",
                                         use_alter=True))

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

class AuthGroup(Base):
    __tablename__ = 'auth_groups'
    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(80), unique=True, nullable=False)
    description = Column(Unicode(255), default=u'')

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, ForeignKey("auth_users.id", "fk_user_authuser", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    status = Column(Unicode(1))

 
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


#class ProjectAcl(Base):
#    __tablename__ = 'authentication_project_acl'
#    rid = Column(Integer,
#                 ForeignKey("projects.id",
#                             name='fk_projectacl_project',
#                             use_alter=True),
#                 primary_key=True)
#    role = Column(Integer,
#                  ForeignKey("authentication_role.id",
#                             name="fk_projectacl_role",
#                             use_alter=True),
#                  primary_key=True)
#    permission = Column(Integer,
#                        ForeignKey("authentication_permission.id",
#                                    name="fk_projectacl_permission",
#                                    use_alter=True,
#                                    ondelete="CASCADE",
#                                    onupdate="CASCADE"),
#                        primary_key=True)
#
#
class ProjectUserRole(Base):
    __tablename__ = 'authentication_project_userrole'
    rid = Column(Integer,
                 ForeignKey("projects.id",
                            name='fk_authentication_project_userrole_project',
                            use_alter=True),
                 primary_key=True)
    role_id = Column(Integer, ForeignKey("authentication_role.id", name="fk_project_userrole_role", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", name="fk_project_userrole_users", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)


class ProjectGroupRole(Base):
    __tablename__ = 'authentication_project_grouprole'
    rid = Column(Integer,
                 ForeignKey("projects.id",
                             name='fk_authentication_project_grouprole_project',
                             use_alter=True),
                 primary_key=True)
    role_id = Column(Integer, ForeignKey("authentication_role.id", name="fk_grouprolerole_role", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"),  primary_key=True)
    group_id = Column(Integer, ForeignKey("auth_groups.id", name="fk_grouprole_group", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)


class Acl(Base):
    __tablename__ = 'authentication_acl'
    role = Column(Integer, ForeignKey("authentication_role.id", name="fk_acl_role", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    permission = Column(Integer, ForeignKey("authentication_permission.id", name="fk_acl_permission", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)


create = [ProjectGroupRole, ProjectUserRole, ]#ProjectAcl]
recreate_constraints = create[:] + [Acl]

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    debug = True
    session.configure(bind=migrate_engine)
    migrate_engine.echo=debug
    metadata.bind = migrate_engine
    metadata.reflect(only=['auth_users'])
    r_meta = s.MetaData(migrate_engine, True)
    def commit():
        session.commit()
        r_meta.bind.execute  ('COMMIT;')
        metadata.bind.execute('COMMIT;') 
    commit()
    for p in create:
        if p.__table__.name in r_meta.tables:
            p.__table__.drop(migrate_engine)
            commit()
        r_meta.reflect()
        p.__table__.create(migrate_engine)
        commit()
    # cleanup old tables inconsistencies
    for acl in Acl.all():
        try:
            perm = Permission.by_id(acl.permission)
        except NoResultFound, e:
            session.delete(acl)
            session.commit()  
            commit()
        except Exception, e:
            pass
    commit()
    r_meta = s.MetaData(migrate_engine, True)
    # create constraints
    fks = []
    for md in recreate_constraints:
        t = md.__table__
        rt = r_meta.tables[t.name]
        rt_constraints = [a for a in rt.foreign_keys]
        for cs in deepcopy(t.foreign_keys):
            if cs.__class__.__name__ == 'ForeignKey':
                if not cs.name in [a.name for a in rt_constraints]:
                    table, column = cs.target_fullname.split('.')
                    target = [r_meta.tables[table].c[column]]
                    parent = [r_meta.tables[cs.parent.table.name].c[cs.parent.name]]
                    fk = ForeignKeyConstraint(columns=parent,refcolumns=target)
                    fk.use_alter = cs.use_alter
                    fk.ondelete = 'CASCADE'
                    fk.onupdate = 'CASCADE'
                    fk.name = cs.name
                    fks.append(fk)

    for fk in fks:
        fk.create(migrate_engine)
        commit()



def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pass
