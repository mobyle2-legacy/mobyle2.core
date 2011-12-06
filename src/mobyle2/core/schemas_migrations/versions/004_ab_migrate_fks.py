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

tables = [user, aclusers, userrole,grouprole,]
from migrate.changeset.constraint import ForeignKeyConstraint

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    # migrate_engine.echo=True
    real_meta = MetaData()
    real_meta.bind = migrate_engine
    real_meta.reflect()
    # remove permission table and underlying fks
    if 'acl_users' in real_meta.tables:
        aclusers.drop()
    if 'acl_users' not in real_meta.tables:
        aclusers.create()
    if 'acl_projects' in real_meta.tables:
        aclprojects.drop()
    if 'acl_projects' not in real_meta.tables:
        aclprojects.create()
    # migrate foreign keys to cascade modifications
    for t in tables:
        rt = real_meta.tables[t.name]
        for ctraint in t.foreign_keys:
            for rctraint in deepcopy(rt.foreign_keys):
                if ((rctraint.name == ctraint.name)
                    or (rctraint.target_fullname == ctraint.target_fullname)):
                    column = rctraint.column
                    parent = rctraint.parent
                    fk = ForeignKeyConstraint([parent], [column], **{'table': rt})
                    fk.name = rctraint.name
                    fk.drop()
    for t in tables:
        rt = real_meta.tables[t.name]
        for ctraint in deepcopy(t.foreign_keys):
            table, c =  ctraint.target_fullname.split('.')
            drc = real_meta.tables[table].c[c]
            parent = ctraint.parent
            fk = ForeignKeyConstraint([parent], [drc], **{'table': rt})
            fk.name = ctraint.name
            fk.use_alter = ctraint.use_alter
            fk.ondelete = ctraint.ondelete
            fk.onupdate = ctraint.onupdate
            fk.create()
    if 'authentication_permission' in real_meta.tables:
        real_meta.tables['authentication_permission'].drop()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pass
