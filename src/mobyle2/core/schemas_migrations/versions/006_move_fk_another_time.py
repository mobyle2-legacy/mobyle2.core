from copy import deepcopy
from sqlalchemy import *
from migrate import *
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship
from migrate.changeset.constraint import ForeignKeyConstraint, PrimaryKeyConstraint

Base = declarative_base()
meta = Base.metadata


class UserRole(Base):
    __tablename__ = 'authentication_userrole'
    user_id = Column(Integer, ForeignKey("users.id", name="fk_userrole_users", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("authentication_role.id", name="fk_userrole_role", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)


class GroupRole(Base):
    __tablename__ = 'authentication_grouprole'
    group_id = Column(Integer, ForeignKey("auth_groups.id", name="fk_grouprole_group", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("authentication_role.id", name="fk_grouprolerole_role", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"),  primary_key=True)
 

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, ForeignKey("auth_users.id", "fk_user_authuser", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    status = Column(Unicode(1))
    base_user = relationship("AuthUser", backref="mobyle_user")
    projects = relationship("Project", uselist=True, backref="user")

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    debug = False
    migrate_engine.echo=debug
    meta.bind = migrate_engine
    real_meta = MetaData()
    real_meta.bind = migrate_engine
    real_meta.reflect()
    rt = real_meta.tables['authentication_userrole']
    for ctraint in deepcopy(rt.foreign_keys):
        if 'fk_userrole_user'  in ctraint.name:
            column = ctraint.column
            parent = ctraint.parent
            fk = ForeignKeyConstraint([parent], [column], **{'table': rt})
            fk.name = ctraint.name
            fk.drop()
    fkp = [a for a in UserRole.__table__.foreign_keys if a.name == 'fk_userrole_users'][0]
    fk = ForeignKeyConstraint([fkp.parent], [fkp.column], **{'table': fkp.parent.table})
    fk.name =      fkp.name
    fk.use_alter = fkp.use_alter
    fk.ondelete =  fkp.ondelete
    fk.onupdate =  fkp.onupdate
    fk.create()
    new_meta = MetaData(bind=migrate_engine)
    new_meta.reflect()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pass
