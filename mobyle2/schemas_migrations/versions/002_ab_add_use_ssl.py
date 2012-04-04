from sqlalchemy import *
from migrate import *



meta = MetaData()
authbackend = Table('authentication_backend', meta,
    Column('use_ssl', Boolean()),
)

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    real_meta = MetaData()
    real_meta.bind = migrate_engine 
    real_meta.reflect()
    if 'use_ssl' not in real_meta.tables['authentication_backend'].c:authbackend.c['use_ssl'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pass
