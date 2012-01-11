import os
from ordereddict import OrderedDict

import shutil
from sqlalchemy import Column
import logging
from sqlalchemy import Unicode
from sqlalchemy import Integer
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from pyramid.security import (
    authenticated_userid,
    Everyone,
    NO_PERMISSION_REQUIRED,
    Allow,
    Authenticated,
    Deny,
)

from mobyle2.core.basemodel import P, R, SecuredObject
from mobyle2.core.models import Base, DBSession as session
from mobyle2.core.utils import _, mobyle2_settings

T, F = True, False
PUBLIC_PROJECT_NAME = 'Public project'
PUBLIC_PROJECT_USERNAME = 'Mobyle2 Public'


default_project_section_acls_mapping = {
    P['project_list']: {R['internal_user'] : T, R['external_user'] : T, R['portal_administrator']:F}
}
default_project_acls_mapping = {
    P['project_view']:    {R['project_watcher'] : T, R['project_contributor'] : T, R['project_owner'] : T, R['project_manager'] : T,},
    P['project_create']:  {R['project_watcher'] : F, R['project_contributor'] : F, R['project_owner'] : T, R['project_manager'] : T,},
    P['project_delete']:  {R['project_watcher'] : F, R['project_contributor'] : F, R['project_owner'] : T, R['project_manager'] : T,},
    P['project_edit']:    {R['project_watcher'] : F, R['project_contributor'] : F, R['project_owner'] : T, R['project_manager'] : T,},
    P['notebook_view']:   {R['project_watcher'] : T, R['project_contributor'] : T, R['project_owner'] : T, R['project_manager'] : T,},
    P['notebook_create']: {R['project_watcher'] : F, R['project_contributor'] : T, R['project_owner'] : T, R['project_manager'] : T,},
    P['notebook_delete']: {R['project_watcher'] : F, R['project_contributor'] : F, R['project_owner'] : T, R['project_manager'] : T,},
    P['notebook_edit']:   {R['project_watcher'] : F, R['project_contributor'] : T, R['project_owner'] : T, R['project_manager'] : T,},
    P['service_view']:    {R['project_watcher'] : T, R['project_contributor'] : T, R['project_owner'] : T, R['project_manager'] : T,},
    P['service_create']:  {R['project_watcher'] : F, R['project_contributor'] : T, R['project_owner'] : T, R['project_manager'] : T,},
    P['service_delete']:  {R['project_watcher'] : F, R['project_contributor'] : F, R['project_owner'] : T, R['project_manager'] : T,},
    P['service_edit']:    {R['project_watcher'] : F, R['project_contributor'] : T, R['project_owner'] : T, R['project_manager'] : T,},
    P['job_run']:         {R['project_watcher'] : F, R['project_contributor'] : T, R['project_owner'] : T, R['project_manager'] : T,},
    P['job_view']:        {R['project_watcher'] : T, R['project_contributor'] : T, R['project_owner'] : T, R['project_manager'] : T,},
    P['job_create']:      {R['project_watcher'] : F, R['project_contributor'] : T, R['project_owner'] : T, R['project_manager'] : T,},
    P['job_delete']:      {R['project_watcher'] : F, R['project_contributor'] : F, R['project_owner'] : T, R['project_manager'] : T,},
    P['job_edit']:        {R['project_watcher'] : F, R['project_contributor'] : T, R['project_owner'] : T, R['project_manager'] : T,},
}
default_projects_acls = []
default_project_acls = []
default_project_roles = []
for k in default_project_acls_mapping:
    for kk in default_project_acls_mapping[k]:
        if not kk in default_project_roles:
            default_project_roles.append(kk)
for m, l in ((default_project_acls_mapping, default_project_acls,),
             (default_project_section_acls_mapping, default_projects_acls),):
    for perm in m:
        permission = m[perm]
        for r in permission:
            if permission[r]:
                spec = Allow
            else:
                spec = Deny
            acl = (spec, r, perm)
            if not acl in l:
                l.append(acl)


class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    description = Column(Unicode(255))
    directory = Column(Unicode(2550))
    user_id = Column(Integer, ForeignKey("users.id", "fk_project_user", use_alter=True))
    owner = relationship("User", primaryjoin="Project.user_id==User.id")
    usersroles = relationship('ProjectUserRole', backref='projets')
    groupsrolesF = relationship('ProjectGroupRole', backref='projects')
    servers = relationship('Server', backref='implied_project', secondary='projects_servers')

    #services = relationship("Service", backref="project", uselist=True)

    @classmethod
    def _projects_dir(self):
        return mobyle2_settings('projects_dir')

    @classmethod
    def projects_dir(self, registry=None):
        return mobyle2_settings('projects_dir', registry=registry)


    def object_acls(self, acls):
        for a in default_project_acls:
            self.append_acl(acls, a)

    def __init__(self, name, description, owner, directory=None, services=None):
        self.name = name
        self.description = description
        self.owner = owner
        self.directory = directory
        if services is not None:
            self.services.extend(services)

    @classmethod
    def logger(self):
        return logging.getLogger('mobyle2.project')

    @classmethod
    def delete(cls, instance):
        logger = Project.logger()
        if instance.directory:
            if os.path.exists(instance.directory):
                try:
                    shutil.rmtree(instance.directory)
                except Exception, e:
                    logger.error('Cant remove directory for instance %s,%s,%s: %s' % (instance.id, instance.name, instance.directory, e))
        try:
            session.delete(instance)
            session.commit()
        except Exception, e:
            logger.error('Cant remove instance %s,%s: %s' % (instance.id, instance.name, e))

    def create_directory(self, registry=None):
        p = self
        if p.id is None:
            raise Exception('Project.create: invalid project state')
        subdir = "%s" % (p.id / 1000)
        pdir = os.path.join(Project.projects_dir(registry=registry), subdir, "%s"%p.id)
        tries = 0
        if os.path.exists(pdir):
            while tries < 10000:
                pdir = os.path.join('%s_%s' % (pdir, tries))
                if not os.path.exists(pdir):
                    break
        if not os.path.exists(pdir):
            os.makedirs(pdir)
            p.directory = pdir
            session.commit()
        else:
            raise Exception('Project directory Alrealdy exists')


    @classmethod
    def create(cls, name=None, description=None, user=None, directory=None, services=None, registry=None):
        p = cls(name, description, user, directory, services)
        session.add(p)
        try:
            session.commit()
        except Exception, e:
            try:
                session.rollback()
            except Exception, e:
                pass
        try:
            if p is not None:
                p.create_directory(registry=registry)
        except Exception, e:
            if p is not None:
                # try to delete a project in an inconsistent state
                try:
                    session.delete(p)
                    session.commit()
                    p = None
                except Exception, e:
                    try:
                        session.rollback()
                    except Exception, e:
                        pass
            raise e
        # give user the owner role
        if p is not None:
            p.make_owner(p.owner)
        return p

    def make_owner(self, user):
        sproject = ProjectRessource(self, None)
        sproject.proxy_roles[R['project_owner']].append_user(user)

    @classmethod
    def by_owner(cls, owner):
        res = []
        prs = session.query(cls).filter_by(owner=owner).all()
        noecho = [res.append(p) for p in prs if not p in res]
        return res

    @classmethod
    def by_participation(cls, usr):
        # fiest get user projects
        res = []
        def uniq_append(items):
            for p in items:
                if not p.resource in res:
                    res.append(p.resource)
        uniq_append(session.query(ProjectUserRole).filter_by(user=usr).all())
        for g in usr.groups:
            uniq_append(session.query(ProjectGroupRole).filter_by(group=g).all())
        return res

    @classmethod
    def get_public_project(cls):
        # leave import there for circular problems
        from mobyle2.core.models import user
        public_user = user.User.search(PUBLIC_PROJECT_USERNAME)
        p = None
        if len(public_user.projects): p = public_user.projects[0]
        return p

class ProjectRessource(SecuredObject):
    __managed_type__ = 'project'
    __managed_roles__ = default_project_roles
    __acl_groups__ = "ProjectGroupRole"
    __acl_users__ = "ProjectUserRole"
    __default_acls__  = default_project_acls
    def __init__(self, p, parent):
        self.project = p
        self.__name__ = "%s" % p.id
        self.__parent__ = parent
        SecuredObject.__init__(self, self.project)


class Projects(SecuredObject):
    __default_acls__  = default_projects_acls
    @property
    def items(self):
        self._items = OrderedDict([("%s" % a.id, ProjectRessource(a, self))
                                   for a in self.session.query(Project).all()])
        return self._items

    def __init__(self, name, parent):
        self.context = self
        self.__name__ = name
        self.__parent__ = parent
        self.__description__ = _("Projects")
        self.request = parent.request
        self.session = parent.session
        SecuredObject.__init__(self)

    def __getitem__(self, item):
        return self.items.get(item, None)




#class ProjectAcl(Base):
#    __tablename__ = 'authentication_project_acl'
#    rid = Column(Integer,
#                 ForeignKey("projects.id",
#                             name='fk_projectacl_project',
#                             use_alter=True),
#                 primary_key=True)
#    role = Column(Integer,
#                  ForeignKey("authentication_role.id",
#                             name="fk_projectacl_role",
#                             use_alter=True),
#                  primary_key=True)
#    permission = Column(Integer,
#                        ForeignKey("authentication_permission.id",
#                                    name="fk_projectacl_permission",
#                                    use_alter=True,
#                                    ondelete="CASCADE",
#                                    onupdate="CASCADE"),
#                        primary_key=True)
#





class ProjectUserRole(Base):
    __tablename__ = 'authentication_project_userrole'
    rid = Column(Integer,
                 ForeignKey("projects.id",
                            name='fk_authentication_project_userrole_project',
                            use_alter=True),
                 primary_key=True)
    role_id = Column(Integer, ForeignKey("authentication_role.id", name="fk_project_userrole_role", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", name="fk_project_userrole_users", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    resource = relationship('Project', backref='mapping_user_role')
    user = relationship('User', backref='mapping_user_role')
    role = relationship('Role', backref='mapping_user_role')

    def __init__(self, resource=None, role=None, user=None):
        Base.__init__(self)
        if resource is not None: self.resource = resource
        if role is not None: self.role = role
        if user is not None: self.user = user

class ProjectGroupRole(Base):
    __tablename__ = 'authentication_project_grouprole'
    rid = Column(Integer,
                 ForeignKey("projects.id",
                             name='fk_authentication_project_grouprole_project',
                             use_alter=True),
                 primary_key=True)
    role_id = Column(Integer, ForeignKey("authentication_role.id", name="fk_grouprolerole_role", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"),  primary_key=True)
    group_id = Column(Integer, ForeignKey("auth_groups.id", name="fk_grouprole_group", use_alter=True, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    resource = relationship('Project', backref='mapping_group_role')
    role    = relationship('Role',    backref='mapping_group_role')
    group   = relationship('Group',
                           backref='mapping_group_role',
                           primaryjoin="ProjectGroupRole.group_id==Group.id",
                           foreign_keys=[group_id])

    def __init__(self, resource=None, role=None, group=None):
        Base.__init__(self)
        if resource is not None: self.resource = resource
        if role is not None: self.role = role
        if group is not None: self.group = group


def create_public_workspace(registry=None):
    project_name = PUBLIC_PROJECT_NAME
    username = PUBLIC_PROJECT_USERNAME
    project_desc = '%s description' % project_name
    user_public_email = '%s@internal' % username
    from apex.models import create_user, AuthUser
    import transaction
    usr = AuthUser.get_by_login(username)
    if usr is None:
        kwargs = {
            'email': user_public_email,
            'username': username,
            'login': username
        }
        if registry:
            kwargs['registry'] = registry
        usr = create_user(**kwargs)
    else:
        usr.username = username
        usr.email = user_public_email
        usr.login = username
        transaction.commit()


