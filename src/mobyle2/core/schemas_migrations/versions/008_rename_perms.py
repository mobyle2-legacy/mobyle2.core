from copy import deepcopy
from sqlalchemy import *
from migrate import *
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm import relationship
from migrate.changeset.constraint import ForeignKeyConstraint, PrimaryKeyConstraint

Base = declarative_base()
meta = Base.metadata


class Permission(Base):
    __tablename__ = 'authentication_permission'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    description = Column(Unicode(2500))

    def __init__(self, id=None, name=None, description=None):
        self.id = id
        self.name = name
        self.description=description

class Role(Base):
    __tablename__ = 'authentication_role'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    description = Column(Unicode(2500))
    global_permissions = relationship(
        "Permission", backref="roles", uselist=True,
        secondary="authentication_acl",
        secondaryjoin="Acl.permission==Permission.id")

class Acl(Base):
    __tablename__ = 'authentication_acl'
    role = Column(Integer, ForeignKey("authentication_role.id", name="fk_acl_role", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    permission = Column(Integer, ForeignKey("authentication_permission.id", name="fk_acl_permission", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)

 
def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    debug = True
    session = scoped_session(sessionmaker())
    session.configure(bind=migrate_engine)
    migrate_engine.echo=debug
    meta.bind = migrate_engine
    real_meta = MetaData()
    real_meta.bind = migrate_engine
    real_meta.reflect()
    mv = {
        'mobyle2 > delete' : 'mobyle2 > global_delete',
        'mobyle2 > edit' : 'mobyle2 > global_edit',
        'mobyle2 > view' : 'mobyle2 > global_view',
        'mobyle2 > create' : 'mobyle2 > global_create',
    }
    pref = 'mobyle2 > '
    dels = ['%s%s' % (pref, suf) for suf in ('global_create',
                                            'global_delete',
                                            'global_edit',
                                            'global_auth')]
    creates = ['%s%s' % (pref, suf) for suf in (('global_authadmin',),
                                                ('global_useradmin',),
                                                ('global_admin',),
                                               )] 
    creates = {
        'mobyle2 > global_admin': 'Administrative access',
        'mobyle2 > global_useradmin': 'Users only administrative access',
        'mobyle2 > global_authadmin': 'Authentication backends only administrative access', 
    }
    for item in mv:
        try:
            perm = session.query(Permission).filter(Permission.name == item).one()
            perm.name = mv[item]
            session.add(perm)
            session.commit()
        except:
            pass
    for item in dels:
        try:
            perm = session.query(Permission).filter(Permission.name == item).one()
            session.delete(perm)
            session.commit()
        except:
            pass
    for item in creates:
        try:
            admin = session.query(Role).filter(Role.name == 'mobyle2 > portal_administrator').one()
            perm = session.query(Permission).filter(Permission.name == item).first()
            if perm is None:
                try:
                    perm = Permission(name=item, description=creates[item])
                    session.add(perm)
                    session.commit()
                except Exception, e:
                    session.rollback()
            if perm is not None:
                if not perm in admin.global_permissions:
                    admin.global_permissions.append(perm)
                    try:
                        session.add(admin)
                        session.commit()
                    except Exception, e:
                        session.rollback() 
        except:
            pass        
def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pass 
