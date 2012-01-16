import logging

from ordereddict import OrderedDict
from mobyle2.core.models import DBSession as session, Base, metadata
from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.orm import relationship
import apex

from pyramid.decorator import reify


from mobyle2.core.models.auth import Role
from mobyle2.core.models.project import Project
from mobyle2.core.basemodel import SecuredObject


from mobyle2.core.utils import _
from apex import models as apexmodels
import mobyle2

user_statuses = {
    'p' : 'Pending',
    'a' : 'Active',
    's' : 'Suspended',
}


class AuthUserGroups(Base):
    __table__ = apexmodels.user_group_table


class Group(Base):
    __table__ = apexmodels.AuthGroup.__table__
    global_roles = relationship(
        "Role", backref="global_groups", uselist=True,
        primaryjoin  ="GroupRole.group_id==Group.id",
        secondaryjoin="GroupRole.role_id==Role.id",
        secondary="authentication_grouprole", )
    users = relationship(
        "User",
        uselist=True,
        primaryjoin  ="AuthUserGroups.group_id==Group.id",
        secondaryjoin="AuthUserGroups.user_id==User.id",
        secondary=    AuthUserGroups.__table__,)


class GroupRole(Base):
    __tablename__ = 'authentication_grouprole'
    role_id = Column(Integer, ForeignKey("authentication_role.id", name="fk_grouprolerole_role", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"),  primary_key=True)
    group_id = Column(Integer, ForeignKey("auth_groups.id", name="fk_grouprole_group", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, ForeignKey(apexmodels.AuthUser.id, "fk_user_authuser", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    status = Column(Unicode(1))
    groups = relationship(
        "Group",
        uselist=True,
        primaryjoin  ="AuthUserGroups.user_id==User.id",
        secondaryjoin="AuthUserGroups.group_id==Group.id",
        secondary=    AuthUserGroups.__table__,)
    projects = relationship("Project", uselist=True)
    global_roles = relationship(
        "Role", backref="global_users", uselist=True,
        secondary="authentication_userrole",
        secondaryjoin="UserRole.role_id==Role.id") 

    @reify
    def base_user(self):
        user = getattr(self, '_base_user_obj', None)
        if user is None:
            setattr(self, '_base_user_obj', apexmodels.AuthUser.get_by_id(self.id))
            user = getattr(self, '_base_user_obj', None)
        return user

    def construct(self):
       base_user = self.base_user
       if not len(self.projects):
            # we do not have yet an project even the default one, 
            # creating the user project
            will, tries, project = -1, 10 , None 
            message = ''
            while tries:
                tries -= 1
                will += 1
                try:
                    pname = 'Default project of %s' % base_user.username
                    if will:
                        pname = '%s (%s)' % (pname, will)
                    project = Project.create(pname, _('Default project created on sign in'), self)
                    break
                except Exception, e:
                    raise
                    message = '%s' % e
                    tries -= 1
            if message:
                error = 'Default project for %s cannot be created' % base_user.username
                if message: error += ' : %s' % message
                logging.getLogger('mobyle2.create_user').error(error)

    def __init__(self, id=None, base_user=None, status=None):
        if (base_user is None) and (id is None):
            raise Exception('must supply id or user')
        if id:
            self.id = id
        elif base_user is not None:
            self.id = base_user.id
        if base_user:
            self.base_user = base_user
        self.status = status
        self.construct()

    def get_status(self):
        user_statuses.get(self.status, None)

    @classmethod
    def search(self, pattern):
        """search by login, then username, then mail"""
        u = None
        try:
            u = apexmodels.AuthUser.get_by_login(pattern)
        except:
            pass
        if u is None:
            try:
                u = apexmodels.AuthUser.get_by_username(pattern)
            except:
                pass 
        if u is None:
            try:
                u = apexmodels.AuthUser.get_by_email(pattern)
            except:
                pass  
        if u is not None:
            u = self.by_id(u.id)
        return u


class UserRole(Base):
    __tablename__ = 'authentication_userrole'
    role_id = Column(Integer, ForeignKey("authentication_role.id", name="fk_userrole_role", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", name="fk_userrole_users", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)

class UserResource(SecuredObject):
    def __init__(self, *args, **kw):
        SecuredObject.__init__(self, *args, **kw)
        self.user = self.context


class Users(SecuredObject):
    __description__ = _("Users") 
    _items = None
    @property
    def items(self):
        if not self._items:
            self._items = OrderedDict([("%s"%a.id, UserResource(a, self, "%s"%id))
                                       for a in self.session.query(User).all()])
        return self._items


