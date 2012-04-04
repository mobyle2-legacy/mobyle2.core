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

    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    debug = True
    session.configure(bind=migrate_engine)
    migrate_engine.echo=debug
    metadata.bind = migrate_engine
    def commit():
        session.commit()
        r_meta.bind.execute  ('COMMIT;')
        metadata.bind.execute('COMMIT;')  
    """ Reload all permissions """
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

    """ Reload all ACLS """
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
    """ Create remote servers table """
    r_meta = s.MetaData(migrate_engine, True)
    Base.metadata.bind = migrate_engine
    for t in [Server.__table__]:
        if not t.name in r_meta.tables: t.create(migrate_engine)
    """Recreate all authentication_acl foreign keys """
    fks = []
    commit()
    for md in [Acl]:
        t = md.__table__
        rt = r_meta.tables[t.name]
        rt_constraints = [a for a in rt.foreign_keys]
        for cs in deepcopy(t.foreign_keys):
            if cs.__class__.__name__ == 'ForeignKey':
                table, column = cs.target_fullname.split('.')
                target = [r_meta.tables[table].c[column]]
                parent = [r_meta.tables[cs.parent.table.name].c[cs.parent.name]]
                fk = ForeignKeyConstraint(columns=parent,refcolumns=target)
                fk.use_alter = cs.use_alter
                fk.ondelete = 'CASCADE'
                fk.onupdate = 'CASCADE'
                fk.name = cs.name
                fks.append(fk)
                if (cs.name in [a.name for a in rt_constraints]
                    or (cs.target_fullname
                        in [a.target_fullname for a in rt_constraints])):
                    fk.drop(migrate_engine)
                    commit()
        for fk in fks:
            fk.create(migrate_engine)
            commit() 

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pass
