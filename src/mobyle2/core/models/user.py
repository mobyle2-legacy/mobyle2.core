from mobyle2.core.models import DBSession, Base
from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.orm import relationship
import apex

from apex.models import AuthUser
import mobyle2

user_statuses = {
    'p' : 'Pending',
    'a' : 'Active',
    's' : 'Suspended',
}


class AuthUser(AuthUser, Base):pass
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, ForeignKey("auth_users.id", "fk_user_authuser", use_alter=True), primary_key=True)
    status = Column(Unicode(1))
    base_user = relationship("AuthUser", backref="mobyle_user")

    def __init__(self, id, status):
        self.id = id
        self.status = status
        self.projects = relationship("Project", backref="user")
        self.abase_user = relationship("AuthUser", backref="mobyle_user")

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
