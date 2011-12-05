from ordereddict import OrderedDict
from mobyle2.core.models import DBSession, Base
from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.orm import relationship
import apex

from mobyle2.core.utils import _
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
class AuthGroup(Base, models.AuthGroup):
    def __init__(self, *args, **kwargs):
        Base.__init__(self, *args, **kwargs)
        models.AuthUser.__init__(self, *args, **kwargs)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, ForeignKey(AuthUser.id, "fk_user_authuser", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    status = Column(Unicode(1))
    base_user = relationship("AuthUser", backref="mobyle_user")
    projects = relationship("Project", uselist=True, backref="user")
    global_roles = relationship(
        "Role", backref="global_users", uselist=True,
        secondary="authentication_userrole",
        secondaryjoin="UserRole.role_id==Role.id")

    def __init__(self, id, status):
        self.id = id
        self.status = status

    def get_status(self):
        user_statuses.get(self.status, None)

class UserRessource(object):
    def __init__(self, p, parent):
        self.user = p
        self.__name__ = "%s"%p.id
        self.__parent__ = parent

class Users:
    @property
    def items(self):
        self._items = OrderedDict([("%s"%a.id, UserRessource(a, self))
                                   for a in self.session.query(User).all()])
        return self._items

    def __init__(self, name, parent):
        self.__name__ = name
        self.__parent__ = parent
        self.__description__ = _("Users")
        self.request = parent.request
        self.session = parent.session

    def __getitem__(self, item):
        return self.items.get(item, None)


class Acl(Base):
    __tablename__ = 'authentication_acl'
    role = Column(Integer, ForeignKey("authentication_role.id", name="fk_acl_role", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    permission = Column(Integer, ForeignKey("authentication_permission.id", name="fk_acl_permission", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)


