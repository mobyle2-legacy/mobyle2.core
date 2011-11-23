from mobyle2.core.models import DBSession, Base
from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.orm import relationship
import apex

from apex import models
import mobyle2

user_statuses = {
    'p' : 'Pending',
    'a' : 'Active',
    's' : 'Suspended',
}

class AuthUser(Base, models.AuthUser):
    def __init__(self, *args, **kwargs):
        Base.__init__(self, *args, **kwargs)
        models.AuthUser.__init__(self, *args, **kwargs)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, ForeignKey(AuthUser.id, "fk_user_authuser", use_alter=True), primary_key=True)
    status = Column(Unicode(1))
    base_user = relationship("AuthUser", backref="mobyle_user")
    projects = relationship("Project", uselist=True, backref="user")

    def __init__(self, id, status):
        self.id = id
        self.status = status

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
