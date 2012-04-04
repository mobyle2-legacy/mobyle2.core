from sqlalchemy import *
from migrate import *

from copy import deepcopy

meta = MetaData()
user = Table(
    'users', meta,
    Column('id', Integer, ForeignKey("auth_users.id", "fk_user_authuser", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
)
aclusers = Table(
    'acl_users', meta,
   Column('role', Integer, ForeignKey("authentication_role.id", name="fk_acl_role", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True),
    Column('permission', Integer, ForeignKey("authentication_permission.id", name="fk_acl_permission", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
)

aclprojects = Table(
    'acl_projects', meta,
    Column('rid', Integer,
                 ForeignKey("projects.id",
                             name='fk_projectacl_project',
                             use_alter=True),
                 primary_key=True),
    Column('role', Integer,
                  ForeignKey("authentication_role.id",
                             name="fk_projectacl_role",
                             use_alter=True),
                  primary_key=True),
    Column('permission', Integer, ForeignKey("authentication_permission.id", name="fk_projectssacl_permission", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True),

)

userrole = Table('authentication_userrole', meta,
                 Column('user_id',Integer, ForeignKey("users.id", name="fk_userrole_user", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True),
                 Column('role_id',Integer, ForeignKey("authentication_role.id", name="fk_userrole_role", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True),
                )

grouprole =  Table('authentication_grouprole', meta,
                   Column('group_id',Integer, ForeignKey("auth_groups.id", name="fk_grouprole_group", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True),
                   Column('role_id',Integer, ForeignKey("authentication_role.id", name="fk_grouprolerole_role", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"),  primary_key=True),
                  )

perm = permission = Table('authentication_permission', meta,
                Column('id', Integer, primary_key=True),
                Column('name', Unicode(50), unique=True),
                Column('description', Unicode(2500)),
               )
tables = [user, aclusers, userrole,grouprole,]
ctables = [perm, aclusers,aclprojects, userrole,grouprole,]

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    # migrate_engine.echo=True
    real_meta = MetaData()
    real_meta.bind = migrate_engine
    real_meta.reflect()
    # remove permission table and underlying fks
    for t in ctables:
        if t.name in real_meta.tables:
            real_meta.tables[t.name].drop()
        t.create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pass
