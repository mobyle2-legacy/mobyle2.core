from mobyle2.core.models.base import Base
from mobyle2.core.models import DBSession
from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.orm import relationship

from apex import models as apex

user_statuses = {
    'p' : 'Pending',
    'a' : 'Active',
    's' : 'Suspended',
}

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, ForeignKey(apex.AuthUser.id), primary_key=True)
    status = Column(Unicode(1))

    def __init__(self, status):
        self.status = status
        self.base_user = relationshipp(apex.AuthUse, backref="mobyle_user")

    def get_status(self):
        user_statuses.get(self.status, None)

def check_login(login, password):
    session = DBSession()
    user = session.query(User).filter_by(userid=login).first()
    if user is not None:
        hashed_password = user.password
        if crypt.check(hashed_password, password):
            return True
    return False
