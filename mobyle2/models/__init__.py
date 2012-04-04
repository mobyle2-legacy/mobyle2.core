# -*- coding: utf-8 -*-

from sqlalchemy import MetaData
from apex import models as apexmodels
from mobyle2.basemodel import DBSession, Base, metadata


"""
SQLAlchemy declarative visitor needed imports
keep the module out of the models namespace as
        it needs to be imported
        without declaring models in the metadata !!!!
"""

import auth
import project
import program
import job
import jobdata
import registry
import user
import workflow
import server
import service


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

