from sqlalchemy import *
from migrate import *

meta = MetaData()


project = Table('project', meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String),
    Column('description', String),
)


users = Table('users', meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('userid', String(20)),
    Column('email', String(50)),
    Column('password', String(255)),
    Column('fullname', String(40)),
    Column('about', String(255)),
    Column('status', String(1)),
    )


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    real_meta = MetaData()
    real_meta.bind = migrate_engine
    real_meta.reflect()
    if 'project' in real_meta.tables:
        project.drop()
    if 'password' in real_meta.tables['users'].c:users.c.password.alter(String(255))
    if 'email' in real_meta.tables['users'].c:users.c.email.alter(String(50))


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    pass
