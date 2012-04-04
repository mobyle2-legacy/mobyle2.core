from copy import deepcopy
from sqlalchemy import *
from migrate import *
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm import relationship
from migrate.changeset.constraint import ForeignKeyConstraint, PrimaryKeyConstraint

Base = declarative_base()
meta = Base.metadata


class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    description = Column(Unicode(255))
    directory = Column(Unicode(2550))
    user_id = Column(Integer, ForeignKey("users.id", "fk_project_user",
                                         use_alter=True))              

 
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
    t = Project.__table__
    rt = real_meta.tables[Project.__table__.name]
    if not 'directory' in rt.c: t.c['directory'].create()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pass  
