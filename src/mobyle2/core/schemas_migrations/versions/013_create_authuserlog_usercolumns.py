
from sqlalchemy import (
    Column,
    Integer,
    Boolean,
    ForeignKey,
    Unicode,
    String,
    Enum,
    types,
)
from copy import deepcopy
import sqlalchemy as s
from sqlalchemy import func
import migrate  as m
from sqlalchemy.orm import relationship
from migrate.changeset.constraint import ForeignKeyConstraint, PrimaryKeyConstraint

from mobyle2.core.basemodel import (
    DBSession, MigrateBase as Base, metadata as metadata,
    MDBSession as session,
    R, P, default_permissions, default_roles, default_acls)



                               


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    debug = True
    session.configure(bind=migrate_engine)
    migrate_engine.echo=debug
    engine = migrate_engine
    r_meta = s.MetaData(migrate_engine, True)
    Base.metadata.bind = migrate_engine

    class AuthUserLog(Base):
        """
        event: 
          L - Login
          R - Register
          P - Password
          F - Forgot
        """
        __tablename__ = 'auth_user_log'
        __table_args__ = {"sqlite_autoincrement": True}

        id = Column(types.Integer, primary_key=True)
        user_id = Column(types.Integer, ForeignKey("auth_users.id"), index=True)
        time = Column(types.DateTime(), default=func.now())
        ip_addr = Column(Unicode(39), nullable=False)
        internal_user = Column(Boolean, nullable=False, default=False)
        external_user = Column(Boolean, nullable=False, default=False)
        event = Column(types.Enum(u'L',u'R',u'P',u'F', name=u"event"), default=u'L') 
    t=AuthUserLog.__table__
    if not 'internal_user' in r_meta.tables[t.name].c: t.c['internal_user'].create(table=t)
    if not 'external_user' in r_meta.tables[t.name].c: t.c['external_user'].create(table=t)

    session.flush()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pass 
