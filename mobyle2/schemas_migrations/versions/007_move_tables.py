from copy import deepcopy
from sqlalchemy import *
from migrate import *
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship
from migrate.changeset.constraint import ForeignKeyConstraint, PrimaryKeyConstraint

Base = declarative_base()
meta = Base.metadata

class Acl(Base):
    __tablename__ = 'authentication_acl'
    role = Column(Integer, ForeignKey("authentication_role.id", name="fk_acl_role", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    permission = Column(Integer, ForeignKey("authentication_permission.id", name="fk_acl_permission", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    debug = False
    migrate_engine.echo=debug
    meta.bind = migrate_engine
    real_meta = MetaData()
    real_meta.bind = migrate_engine
    real_meta.reflect()
    if not 'authentication_acl' in real_meta.tables: Acl.__table__.create()
    if 'acl_users' in real_meta.tables: real_meta.tables['acl_users'].drop()
    new_meta = MetaData(bind=migrate_engine)
    new_meta.reflect()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pass
