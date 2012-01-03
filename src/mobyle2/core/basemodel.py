#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
"""
This module contains base objects and constants for all models objects

SQLAlchemy declarative visitor needed import everything under the models
namespace.
keep the module out of the models namespace as
It needs to be imported  without declaring models in the metadata !!!!
"""

from pyramid.interfaces import IStaticURLInfo
from pyramid.decorator import reify
from pyramid.security import (
    authenticated_userid,
    Everyone,
    NO_PERMISSION_REQUIRED,
    ALL_PERMISSIONS,
    Allow, Deny,
    Authenticated,
)

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from mobyle2.core.utils import _




DBSession = scoped_session(sessionmaker())
MDBSession = scoped_session(sessionmaker())
class AbstractModel(object):
    session = DBSession
    @classmethod
    def by_name(cls, name):
        return cls.session.query(cls).filter(cls.name==name).one()
    @classmethod
    def by_id(cls, id):
        return cls.session.query(cls).filter(cls.id==int(id)).one()
    @classmethod
    def all(cls):
        return cls.session.query(cls).all()



class MigrateAbstractModel(AbstractModel):
    session = MDBSession
    __table_args__ = {'keep_existing':True}


def acl_for_role_proxy_factory(self, rolename, acluser, aclgroup):
    """Please note that role is lazy loaded"""
    #let this import in the factory scope
    # to avoid circular import problems
    session = DBSession
    class Proxy:
        _role = None
        @property
        def role(self):
            from mobyle2.core.models.auth import Role
            if self._role is None:
                self._role = session.query(Role).filter_by(name=rolename).one()
            return self._role

        def append_group(p, item):
            if aclgroup is None: return
            if not p.has_group(item):
                i = aclgroup(role=p.role, group=item, resource=self.context)
                session.add(i)
                session.commit()

        def remove_group(p, item):
            if aclgroup is None: return
            if p.has_group(item):
                to_del = self._role = session.query(aclgroup).filter_by(
                    role=p.role,
                    resource=self.context,
                    group=item).all()
                deleted, modified = [], False
                for a in to_del:
                    if not a in deleted:
                        session.delete(a)
                        deleted.append(a)
                if modified:
                    session.commit()


        def append_user(p, item):
            if acluser is None: return
            if not p.has_user(item):
                i = acluser(role=p.role, user=item, resource=self.context)
                session.add(i)
                session.commit()

        def remove_user(p, item):
            if acluser is None: return
            if p.has_user(item):
                to_del = self._role = session.query(acluser).filter_by(
                    role=p.role,
                    resource=self.context,
                    user=item).all()
                deleted, modified = [], False
                for a in to_del:
                    if not a in deleted:
                        session.delete(a)
                        deleted.append(a)
                if modified:
                    session.commit()
        @property
        def list_users(p):
            l = []
            if acluser is not None:
                l =  self.users_for_role(p.role)
            return l
        @property
        def list_groups(p):
            l = []
            if aclgroup is not None:
                l =  self.groups_for_role(p.role)
            return l
        def has_user(p, usr):
            return usr in p.list_users
        def has_group(p, grp):
            return grp in p.list_groups
    return Proxy()

class SecuredObject(object):
    """Base Mixin to implement object security with acl and roles mangement
    by using two separated tables containing acls for users & groups.
    You ll have an object with security related methods and proxy wrappers to manage role assigments.

    It would have been better to also integrate a Ressource Mixin from which
    objects would have inherited and get the (user,group) from there with the joined inheritance.

    Note that it uses mobyle2.core rolenaming scheme (resourcetype_rolename registration in the 'R' dict)


    You just have to
        - Make the 2 users/groups acl mapping models
        - inhefit from this mixin and set the appripriate properties on the object


    R['foo_myrole'] = 'mobyle2 > foo_contributor'

    class FooUserRole(Base):
        __tablename__ = 'authentication_foo_userrole'
        rid = Column(Integer,
                     ForeignKey("foos.id",
                                name='fk_authentication_foo_userrole_foo',
                                use_alter=True),
                     primary_key=True)
        role_id = Column(Integer, ForeignKey("authentication_role.id", name="fk_foo_userrole_role", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
        user_id = Column(Integer, ForeignKey("users.id", name="fk_foo_userrole_users", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
        resource = relationship('Foo', backref='mapping_user_role')
        user = relationship('User', backref='mapping_user_role')
        role = relationship('Role', backref='mapping_user_role')
        def __init__(self, resource=None, role=None, user=None):
            Base.__init__(self)
            if resource is not None: self.resource = resource
            if role is not None: self.role = role
            if user is not None: self.user = user


    class FooGroupRole(Base):
        __tablename__ = 'authentication_foo_grouprole'
        rid = Column(Integer,
                     ForeignKey("foos.id",
                                 name='fk_authentication_foo_grouprole_foo',
                                 use_alter=True),
                     primary_key=True)
        role_id = Column(Integer, ForeignKey("authentication_role.id", name="fk_grouprolerole_role", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"),  primary_key=True)
        group_id = Column(Integer, ForeignKey("auth_groups.id", name="fk_grouprole_group", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
        resource = relationship('Foo', backref='mapping_group_role')
        role    = relationship('Role',    backref='mapping_group_role')
        group   = relationship('Group',
                               backref='mapping_group_role',
                               primaryjoin="FooGroupRole.group_id==Group.id",
                               foreign_keys=[group_id])
        def __init__(self, resource=None, role=None, group=None):
            Base.__init__(self)
            if resource is not None: self.resource = resource
            if role is not None: self.role = role
            if group is not None: self.group = group


    class Foo(Base):
        id = Column(Integer, primary_key=True)


    class Securedfoo(SecuredObject):
        __managed_roles__ = [R['foo_myrole']]
        __acl_users__ = 'FooUserRole'
        __acl_groups = 'FooGroupRole'
        def __init__(self, p, parent):
            self.foo = p
            self.__name__ = "%s" % p.id
            self.__parent__ = parent
            SecuredObject.__init__(self, self.foo)


    Example:

        >>> foo = Foo()
        >>> sfoo = Securedfoo(Foo)
        >>> u1 = session.query(User).first()
        >>> sfoo.myrole.append_user(u1)
        >>> [u1] == sfoo.myrole.list_users
        >>> True == sfoo.myrole.has_user(u1)
        >>> sfoo.myrole.remove_user(u1)
        >>> False == sfoo.myrole.has_user(u1)
        >>> g1 = session.query(Group).first()
        >>> [g1] == sfoo.myrole.list_groups
        >>> sfoo.myrole.append_group(g1)
        >>> False == sfoo.myrole.has_user(u1)
        >>> sfoo.myrole.remove_group(g1)
        >>> False == sfoo.myrole.has_group(u1)
        >>> True == R['foo_myrole'] in sfoo.get_roles_for_user(u1)
        >>> True == R['foo_myrole'] in sfoo.get_roles_for_group(g1)

    """
    __managed_roles__ = []
    """List of roles as string, those roles are the
    resource specific roles to create proxy for"""
    __acl_users__ = None
    """Acl table to find users/role/user mappings (rid/user_id/role_id)
    type is either a string of the sqlalchemy model or directly the model
    """
    __acl_groups__ = None
    """Acl table to find groups/role/user mappings (rid/group_id/role_id)
    type is either a string of the sqlalchemy model or directly the model
    """
    __default_acls__ = []
    """Default access list, see pyramid.security acl stuff and the __acl__ method in this class"""

    def __init__(self, context=None):
        self.context = context
        self.acluser = self.__acl_users__
        self.aclgroup = self.__acl_groups__
        if isinstance(self.acluser, basestring):
            self.acluser = Base._decl_class_registry[self.acluser]
        if isinstance(self.aclgroup, basestring):
            self.aclgroup = Base._decl_class_registry[self.aclgroup]
        self.proxy_roles = {}
        for role in self.__managed_roles__:
            self.proxy_roles[role] = acl_for_role_proxy_factory(
                self, role, self.acluser, self.aclgroup)

    def users_for_role(self, role):
        """All user/role mappings for this resource"""
        l = []
        if self.acluser is not None:
            l = [a.user
                 for a in DBSession.query(
                     self.acluser).filter_by(
                         resource=self.context, role=role).all()]
        return l

    def groups_for_role(self, role):
        """All group/role mappings for this resource"""
        l = []
        if self.aclgroup is not None:
            l = [a.group
                 for a in DBSession.query(
                     self.aclgroup).filter_by(
                         resource=self.context, role=role).all()]
        return l

    def get_roles_for_user(self, usr):
        l = []
        if self.acluser is not None:
            l = [a.role
                 for a in DBSession.query(
                     self.acluser).filter_by(
                         resource=self.context, user=usr).all()]
        return l

    def get_roles_for_group(self, grp):
        l = []
        if self.aclgroup is not None:
            l = [a.role
                 for a in DBSession.query(
                     self.aclgroup).filter_by(
                         resource=self.context, group=grp).all()]
        return l

    #@reify
    #def user(self):
    #    request = self.request
    #    registry = request.registry
    #    usr, uid = None, authenticated_userid(self.request)
    #    if uid:
    #        usr = user.User.by_id(uid)
    #    return usr

    def object_acls(self, acls):
        """Additionnal hook to search for dynamic acl in subclass"""

    def append_acl(self, acls, acl):
        if acl[0] == Allow:
            acls.insert(0, acl)
        if acl[0] == Deny:
            acls.append(acl)
        return acls

    @reify
    def __acl__(self):
        request = self.request
        registry = request.registry
        uid = authenticated_userid(self.request)
        static_permission = [(Allow, Everyone, 'view'),
                              (Allow, Authenticated, 'authenticated')]
        static_subpaths = [a[2]
                           for a in registry.queryUtility(
                               IStaticURLInfo)._get_registrations(registry)]
        # special case: handle static views
        acls = [(Allow, Everyone, NO_PERMISSION_REQUIRED),
                (Allow, R['portal_administrator'], ALL_PERMISSIONS)]
        load = True
        if request.matched_route:
            # only skip acl matching if we are in static
            if request.matched_route in static_subpaths:
                acls.append(static_permission)
                load = False
        # otherwise going with business permissions
        if load:
            for a in self.__default_acls__:
                if not a in acls:
                    self.append_acl(acls, a)
            self.object_acls(acls)
        """
         never place that at the end of your acls because it will
         stop inheriting from parent acls by denying immediatly
         any access to the current context resource.

            self.append_acl(acls, (Deny, Everyone, ALL_PERMISSIONS))

        """
        return acls


Base = declarative_base(cls=AbstractModel)
MigrateBase = declarative_base(cls=MigrateAbstractModel)
metadata = meta = Base.metadata
migrate_metadata = mmeta = MigrateBase.metadata

T, F = True, False


ANONYMOUS_ROLE = 'mobyle2 > anonyme'

R = {
    'anonyme': ANONYMOUS_ROLE,
    'internal_user'         : 'mobyle2 > internal_user',
    'external_user'         : 'mobyle2 > external_user',
    'project_owner'         : 'mobyle2 > project_owner',
    'project_watcher'       : 'mobyle2 > project_watcher',
    'project_contributor'   : 'mobyle2 > project_contributor',
    'project_manager'       : 'mobyle2 > project_manager',
    'portal_administrator'  : 'mobyle2 > portal_administrator',

}


default_roles = {
    ANONYMOUS_ROLE : _('Anonym'),
    R['internal_user'] : _('Internal user'),
    R['external_user'] : _('External user'),
    R['project_owner'] : _('Project owner'),
    R['project_watcher'] : _('Project watcher'),
    R['project_contributor'] : _('Project contributor'),
    R['project_manager'] : _('Project manager'),
    R['portal_administrator'] : _('Portal administrator'),
}
# shortcuts
P = {
    "global_authadmin": 'mobyle2 > global_authadmin',
    "global_useradmin": 'mobyle2 > global_useradmin',
    "global_admin":     'mobyle2 > global_admin',
    "global_view":      'mobyle2 > global_view',
    "group_create":     'mobyle2 > group_create',
    "group_delete":     'mobyle2 > group_delete',
    "group_edit":       'mobyle2 > group_edit',
    "group_view":       'mobyle2 > group_view',
    "user_create":      'mobyle2 > user_create',
    "user_delete":      'mobyle2 > user_delete',
    "user_edit":        'mobyle2 > user_edit',
    "user_view":        'mobyle2 > user_view',
    "project_editperm":     'mobyle2 > project_editperm',
    "project_list":     'mobyle2 > project_list',
    "project_view":     'mobyle2 > project_view',
    "project_create":   'mobyle2 > project_create',
    "project_delete":   'mobyle2 > project_delete',
    "project_edit":     'mobyle2 > project_edit',
    "notebook_view":    'mobyle2 > notebook_view',
    "notebook_create":  'mobyle2 > notebook_create',
    "notebook_delete":  'mobyle2 > notebook_delete',
    "notebook_edit":    'mobyle2 > notebook_edit',
    "service_view":     'mobyle2 > service_view',
    "service_create":   'mobyle2 > service_create',
    "service_delete":   'mobyle2 > service_delete',
    "service_edit":     'mobyle2 > service_edit',
    "job_run":          'mobyle2 > job_run',
    "job_view":         'mobyle2 > job_view',
    "job_create":       'mobyle2 > job_create',
    "job_delete":       'mobyle2 > job_delete',
    "job_edit":         'mobyle2 > job_edit',
}

default_permissions = {
    P['global_admin']: _('Administrative access'),
    P['project_editperm']: _('Manage project permissions'),
    P['global_useradmin']: _('Users only administrative access'),
    P['global_authadmin']: _('Authentication backends only administrative access'),
    P['global_view']: _('View access'),
    P['project_list']: _('List projects'),
    P['project_view']: _('View project'),
    P['project_create']: _('Create project'),
    P['project_delete']: _('Delete project'),
    P['project_edit']:   _('Edit project'),
    P['notebook_view']: _('View notebook'),
    P['notebook_create']: _('Create notebook'),
    P['notebook_delete']: _('Delete notebook'),
    P['notebook_edit']:   _('Edit notebook'),
    P['service_view']: _('View service'),
    P['service_create']: _('Create service'),
    P['service_delete']: _('Delete service'),
    P['service_edit']:   _('Edit service'),
    P['job_run']: _('Run job'),
    P['job_view']: _('View job'),
    P['job_create']: _('Create job'),
    P['job_delete']: _('Delete job'),
    P['job_edit']:   _('Edit job'),
}

default_acls = {
    P['global_view']:      {R['project_watcher'] : T, R['project_contributor'] : T, R['anonyme'] : T, R['internal_user'] : T, R['external_user'] : T, R['project_owner'] : T, R['project_manager'] : T, R['portal_administrator'] : T,},
    P['global_admin']:     {R['project_watcher'] : F, R['project_contributor'] : F, R['anonyme'] : F, R['internal_user'] : F, R['external_user'] : F, R['project_owner'] : F, R['project_manager'] : F, R['portal_administrator'] : T,},
    P['global_authadmin']: {R['project_watcher'] : F, R['project_contributor'] : F, R['anonyme'] : F, R['internal_user'] : F, R['external_user'] : F, R['project_owner'] : F, R['project_manager'] : F, R['portal_administrator'] : T,},
    P['global_useradmin']: {R['project_watcher'] : F, R['project_contributor'] : F, R['anonyme'] : F, R['internal_user'] : F, R['external_user'] : F, R['project_owner'] : F, R['project_manager'] : F, R['portal_administrator'] : T,},
    P['project_list']:     {R['project_watcher'] : F, R['project_contributor'] : F, R['anonyme'] : F, R['internal_user'] : F, R['external_user'] : F, R['project_owner'] : F, R['project_manager'] : F, R['portal_administrator'] : F,},
    P['project_view']:     {R['project_watcher'] : T, R['project_contributor'] : T, R['anonyme'] : T, R['internal_user'] : F, R['external_user'] : F, R['project_owner'] : T, R['project_manager'] : T, R['portal_administrator'] : T,},
    P['project_editperm']: {R['project_watcher'] : F, R['project_contributor'] : F, R['anonyme'] : F, R['internal_user'] : F, R['external_user'] : F, R['project_owner'] : T, R['project_manager'] : T, R['portal_administrator'] : T,},
    P['project_create']:   {R['project_watcher'] : F, R['project_contributor'] : F, R['anonyme'] : F, R['internal_user'] : T, R['external_user'] : T, R['project_owner'] : T, R['project_manager'] : T, R['portal_administrator'] : T,},
    P['project_delete']:   {R['project_watcher'] : F, R['project_contributor'] : F, R['anonyme'] : F, R['internal_user'] : F, R['external_user'] : F, R['project_owner'] : T, R['project_manager'] : T, R['portal_administrator'] : T,},
    P['project_edit']:     {R['project_watcher'] : F, R['project_contributor'] : F, R['anonyme'] : F, R['internal_user'] : F, R['external_user'] : F, R['project_owner'] : T, R['project_manager'] : T, R['portal_administrator'] : T,},
    P['notebook_view']:    {R['project_watcher'] : T, R['project_contributor'] : T, R['anonyme'] : T, R['internal_user'] : F, R['external_user'] : F, R['project_owner'] : T, R['project_manager'] : T, R['portal_administrator'] : T,},
    P['notebook_create']:  {R['project_watcher'] : F, R['project_contributor'] : T, R['anonyme'] : F, R['internal_user'] : F, R['external_user'] : F, R['project_owner'] : T, R['project_manager'] : T, R['portal_administrator'] : T,},
    P['notebook_delete']:  {R['project_watcher'] : F, R['project_contributor'] : F, R['anonyme'] : F, R['internal_user'] : F, R['external_user'] : F, R['project_owner'] : T, R['project_manager'] : T, R['portal_administrator'] : T,},
    P['notebook_edit']:    {R['project_watcher'] : F, R['project_contributor'] : T, R['anonyme'] : F, R['internal_user'] : F, R['external_user'] : F, R['project_owner'] : T, R['project_manager'] : T, R['portal_administrator'] : T,},
    P['service_view']:     {R['project_watcher'] : T, R['project_contributor'] : T, R['anonyme'] : T, R['internal_user'] : F, R['external_user'] : F, R['project_owner'] : T, R['project_manager'] : T, R['portal_administrator'] : T,},
    P['service_create']:   {R['project_watcher'] : F, R['project_contributor'] : T, R['anonyme'] : F, R['internal_user'] : F, R['external_user'] : F, R['project_owner'] : T, R['project_manager'] : T, R['portal_administrator'] : T,},
    P['service_delete']:   {R['project_watcher'] : F, R['project_contributor'] : F, R['anonyme'] : F, R['internal_user'] : F, R['external_user'] : F, R['project_owner'] : T, R['project_manager'] : T, R['portal_administrator'] : T,},
    P['service_edit']:     {R['project_watcher'] : F, R['project_contributor'] : T, R['anonyme'] : F, R['internal_user'] : F, R['external_user'] : F, R['project_owner'] : T, R['project_manager'] : T, R['portal_administrator'] : T,},
    P['job_run']:          {R['project_watcher'] : F, R['project_contributor'] : T, R['anonyme'] : F, R['internal_user'] : F, R['external_user'] : F, R['project_owner'] : T, R['project_manager'] : T, R['portal_administrator'] : T,},
    P['job_view']:         {R['project_watcher'] : T, R['project_contributor'] : T, R['anonyme'] : T, R['internal_user'] : F, R['external_user'] : F, R['project_owner'] : T, R['project_manager'] : T, R['portal_administrator'] : T,},
    P['job_create']:       {R['project_watcher'] : F, R['project_contributor'] : T, R['anonyme'] : F, R['internal_user'] : F, R['external_user'] : F, R['project_owner'] : T, R['project_manager'] : T, R['portal_administrator'] : T,},
    P['job_delete']:       {R['project_watcher'] : F, R['project_contributor'] : F, R['anonyme'] : F, R['internal_user'] : F, R['external_user'] : F, R['project_owner'] : T, R['project_manager'] : T, R['portal_administrator'] : T,},
    P['job_edit']:         {R['project_watcher'] : F, R['project_contributor'] : T, R['anonyme'] : F, R['internal_user'] : F, R['external_user'] : F, R['project_owner'] : T, R['project_manager'] : T, R['portal_administrator'] : T,},
}


# vim:set et sts=4 ts=4 tw=0:
