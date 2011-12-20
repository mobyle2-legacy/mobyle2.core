# -*- coding: utf-8 -*-
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import MetaData
from apex import models as apexmodels


class AbstractModel(object):
    @classmethod
    def by_name(cls, name):
        return DBSession.query(cls).filter(cls.name==name).one()
    @classmethod
    def by_id(cls, id):
        return DBSession.query(cls).filter(cls.id==int(id)).one()
    @classmethod
    def all(cls):
        return DBSession.query(cls).all()

DBSession = scoped_session(sessionmaker())
Base = declarative_base(cls=AbstractModel)
metadata = Base.metadata


"""
SQLAlchemy declarative visitor needed imports
"""

import auth
import project
import program
import job
import jobdata
import registry
import user
import workflow


def initialize_sql(engine, create=False):
    """Moved from init to avoid circular imports"""
    real_meta = MetaData(engine, reflect=True)
    apex_tables = ['auth_users', 'auth_groups']
    tables = ['users',
              'projects',
              'authentication_backend',
              'authentication_acl',
              'authentication_role',
              'authentication_grouprole',
              'authentication_userrole',
              'authentication_permission',
              'jobs']
    apex_create = False
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    apexmodels.Base.metadata.bind = engine
    def reflect():
        Base.metadata.reflect(engine)
        apexmodels.Base.metadata.reflect()
    for t in apex_tables:
        if not t in real_meta.tables:
            apex_create = True
    for t in tables:
        if not t in real_meta.tables:
            create = True
    if apex_create:
        user.GroupRole.__table__.create(engine)
        apexmodels.Base.metadata.create_all(engine)
        reflect()
    if create:
        Base.metadata.create_all(engine)
        reflect()
    if apex_create:
        apexmodels.initialize_sql(engine)
        reflect()
    reflect()
    registry.register_default_keys(DBSession)
    auth.register_default_permissions(DBSession)
    auth.register_default_roles(DBSession)
    auth.register_default_acls(DBSession)


