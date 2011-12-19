from mobyle2.core.models import DBSession
from mobyle2.core.models import Base
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
        if isinstance(default, NotSet):
            raise
        else:
            res = default
    return res

def set_registry_key(key, value):
    session = DBSession()
    res = None
    try:
        try:
            res = session.query(Registry).filter(Registry.name == key).one()
            res.value = value
        except exc.NoResultFound, e:
            res = Registry(key, value)
            session.add(res)
        session.commit()
    except exc.NoResultFound, e:
        raise
    return res
             

def register_default_keys(session, force=False):
    # authentication settings
    if not force:
        force = not get_registry_key('mobyle2.configured_keys', False)
    if not force:
        return  
    default_keys = {
        'auth.allow_anonymous': 'false',
        'auth.use_captcha': 'false',
        'auth.self_registration': 'false',
        'auth.recaptcha_private_key': None,
        'auth.recaptcha_public_key': None,
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
    set_registry_key('mobyle2.configured_keys', "1")
    session.flush()

