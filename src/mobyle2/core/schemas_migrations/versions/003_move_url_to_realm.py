from sqlalchemy import *
from migrate import *


meta = MetaData()
authbackend = Table('authentication_backend', meta,
                    Column('url_ba', Unicode(255)),
                    Column('realm', Unicode(255)),
)

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    real_meta = MetaData()
    real_meta.bind = migrate_engine
    real_meta.reflect()
    if 'url_ba' in real_meta.tables['authentication_backend'].c:authbackend.c['url_ba'].drop()
    if 'realm' not in real_meta.tables['authentication_backend'].c:authbackend.c['realm'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    if 'url_ba'not in real_meta.tables['authentication_backend'].c:authbackend.c['url_ba'].create()
    if 'realm' in real_meta.tables['authentication_backend'].c:authbackend.c['realm'].drop()



