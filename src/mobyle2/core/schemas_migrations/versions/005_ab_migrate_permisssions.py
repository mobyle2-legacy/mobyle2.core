from sqlalchemy import *
from migrate import *

from copy import deepcopy

meta = MetaData()
aclusers = Table(
    'acl_users', meta,
    Column('permission', Integer),
)
aclprojects = Table(
    'acl_projects', meta,
    Column('permission', Integer),
)
permission = Table('authentication_permission', meta,
                    Column('id', Integer, primary_key=True),
                    Column('name', Unicode(50), unique=True),
                    Column('description', Unicode(2500)),
                   )
from migrate.changeset.constraint import ForeignKeyConstraint, PrimaryKeyConstraint

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    debug = False
    migrate_engine.echo=debug
    meta.bind = migrate_engine
    real_meta = MetaData()
    real_meta.bind = migrate_engine
    real_meta.reflect()
    # finally i decided to go to a separate permission table
    if 'authentication_permission' not in real_meta.tables:
        permission.create()
    for acl, item in ((aclusers, 'users'), (aclprojects, 'projects')):
        rt = real_meta.tables[acl.name]
        for ctraint in deepcopy(rt.foreign_keys):
            if ('perm' in ctraint.name) or ('perm' in ctraint.parent.name):
                column = ctraint.column
                parent = ctraint.parent
                fk = ForeignKeyConstraint([parent], [column], **{'table': rt})
                fk.name = ctraint.name
                fk.drop()
        if 'permission' in rt.c:
            if len(rt.c["permission"].foreign_keys) > 0:
                rt.c["permission"].drop()
        if 'permission' in rt.c:
            ctype = rt.c['permission'].type.__class__.__name__
            drop = False
            if 'CHAR' in ctype:
                drop = True
            if 'INTEGER' in ctype:
                drop = True
            if drop:
                rt.c["permission"].drop()
        if not ('permission' in rt.c):
            acl.c["permission"].create()
        # refresh metA
        fkp = {"users":ForeignKey("authentication_permission.id", name="fk_userssacl_permission", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"),
              "projects":ForeignKey("authentication_permission.id", name="fk_projectsacl_permission", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"),
             }.get(item)
        fk = ForeignKeyConstraint([acl.c.permission], [permission.c.id], **{'table': acl})
        fk.name =      fkp.name
        fk.use_alter = fkp.use_alter
        fk.ondelete =  fkp.ondelete
        fk.onupdate =  fkp.onupdate
        fk.create()
        new_meta = MetaData(bind=migrate_engine)
        new_meta.reflect()
        nt = new_meta.tables[acl.name]
        columns = []
        if 'project' in item:
            columns.append(nt.c['rid'])
        columns.extend([nt.c['role'], nt.c['permission']])
        pk = PrimaryKeyConstraint(*columns)
        pk.create()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pass
