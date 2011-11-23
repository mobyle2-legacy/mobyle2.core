from mobyle2.core.models import DBSession
from mobyle2.core.models.base import Base
from mobyle2.core.utils import asbool
from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import Integer
from sqlalchemy.orm import exc

class Registry(Base):
    __tablename__ = 'registry'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), unique=True)
    value = Column(Unicode(255))

    def __init__(self, name='', value=''):
        self.name = name
        self.value = value

def register_default_keys(session):
    # authentication settings
    default_keys = {
        'auth.allow_anonymous': 'false',
        'auth.use_captcha': 'false',
        'auth.self_registration': 'false',
    }
    for k in default_keys:
        try:
            session.query(Registry).filter(Registry.name == k).one()
        except exc.NoResultFound, e:
            try:
                session.add(
                    Registry(k, default_keys[k])
                )
                session.commit()
            except exc.IntegrityError:
                session.rollback()
    session.flush()

class NotSet(object):pass
notset = NotSet()

def get_registry_key(key, default=notset, as_bool=True):
    session = DBSession()
    res = None
    try:
        res = session.query(Registry).filter(Registry.name == key).one().value
        if as_bool:
            res = asbool(res)
    except exc.NoResultFound, e:
        if isinstance(default, notset):
            raise
        else:
            res = default
    return res

