from sqlalchemy import (
    Column,
    Integer,
    Boolean,
    ForeignKey,
    Unicode,
    DateTime,
    String,
    Enum,
)

import sqlalchemy.sql.functions as func

from copy import deepcopy
import sqlalchemy as s
from migrate import *
from sqlalchemy.orm import relationship

from migrate.changeset.constraint import ForeignKeyConstraint, PrimaryKeyConstraint

from mobyle2.basemodel import (
    DBSession, MigrateBase as Base, mmeta as metadata,
    MDBSession as session,
    R, P, default_permissions, default_roles, default_acls)

from sqlalchemy.orm.exc import NoResultFound


def upgrade(migrate_engine):
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

        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey("auth_users.id", onupdate='CASCADE', ondelete='CASCADE'), index=True)
        time = Column(DateTime(), default=func.now())
        ip_addr = Column(Unicode(39), nullable=False)
        internal_user = Column(Boolean, nullable=False, default=False)
        external_user = Column(Boolean, nullable=False, default=False)
        event = Column(Enum(u'L',u'R',u'P',u'F', name=u"event"), default=u'L')

    recreate_constraints = [AuthUserLog]
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    debug = True
    session.configure(bind=migrate_engine)
    migrate_engine.echo=debug
    metadata.bind = migrate_engine
    metadata.reflect(only=['auth_users'])
    r_meta = s.MetaData(migrate_engine, True)
    def commit():
        session.commit()
        r_meta.bind.execute  ('COMMIT;')
        metadata.bind.execute('COMMIT;')
    # create constraints
    fks = []
    for md in recreate_constraints:
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
