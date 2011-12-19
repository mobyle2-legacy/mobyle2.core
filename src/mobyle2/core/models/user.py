from ordereddict import OrderedDict
from mobyle2.core.models import DBSession as session, Base, metadata
from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.orm import relationship
import apex

from pyramid.decorator import reify


from mobyle2.core.models.auth import Role, GroupRole, UserRole


from mobyle2.core.utils import _
from apex import models
import mobyle2

user_statuses = {
    'p' : 'Pending',
    'a' : 'Active',
    's' : 'Suspended',
}

tauth_users = models.AuthUser.metadata.tables[models.AuthUser.__table__.name]
tauth_groups = models.AuthUser.metadata.tables[models.AuthGroup.__table__.name]


class Group(Base):
    __table__ = tauth_groups
    global_roles = relationship(
        "Role", backref="global_groups", uselist=True,
        primaryjoin  ="GroupRole.group_id==Group.id",
        secondaryjoin="GroupRole.role_id==Role.id",
        secondary="authentication_grouprole", )
    users = relationship(
        "User", 
        uselist=True,
        primaryjoin  ="auth_user_groups.c.group_id==Group.id",
        secondaryjoin="auth_user_groups.c.user_id== User.id",
        secondary="auth_user_groups", )


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, ForeignKey(models.AuthUser.id, "fk_user_authuser", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    status = Column(Unicode(1))
    groups = relationship(
        "Group", 
        uselist=True,
        primaryjoin  ="auth_user_groups.c.user_id==User.id",
        secondaryjoin="auth_user_groups.c.group_id== Group.id",
        secondary="auth_user_groups",) 

    @reify
    def base_user(self):
        user = getattr(self, '_base_user_obj', None)
        if user is None:
            setattr(self, '_base_user_obj', models.AuthUser.get_by_id(self.id))
            user = getattr(self, '_base_user_obj', None)
        return user

    projects = relationship("Project", uselist=True, backref="user")
    global_roles = relationship(
        "Role", backref="global_users", uselist=True,
        secondary="authentication_userrole",
        secondaryjoin="UserRole.role_id==Role.id")

    def __init__(self, user=None, id=None, status=None):
        if (user is None) and (id is None):
            raise Exception('must supply id or user')
        if id:
            self.id = id
        if user:
            self.base_user = user
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



