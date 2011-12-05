# -*- coding: utf-8 -*-
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DBSession = scoped_session(sessionmaker())
Base = declarative_base()

"""
SQLAlchemy declarative visitor needed imports
"""

import auth
import project
import job
import jobdata
import registry
import user
import workflow

def initialize_sql(engine):
    """Moved from init to avoid circular imports"""
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.reflect(engine)
    Base.metadata.create_all(engine)
    registry.register_default_keys(DBSession)
    auth.register_default_permissions(DBSession)
    auth.register_default_roles(DBSession)
