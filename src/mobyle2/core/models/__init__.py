from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
DBSession = scoped_session(sessionmaker())
Base = declarative_base()

from auth import AuthenticationBackend, AuthenticationBackends
from project import Project
from job import Job
from registry import Registry
from user import User
from workflow import Workflow
from apex.models import AuthUser

def initialize_sql(engine):
    """Moved from init to avoid circular imports"""
    DBSession.configure(bind=engine)
    import mobyle2
    Base.metadata.bind = engine
    Base.metadata.reflect(engine)
    Base.metadata.create_all(engine)
    registry.register_default_keys(DBSession)
