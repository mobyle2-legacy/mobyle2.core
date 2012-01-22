import logging
import os
from copy import deepcopy
from ordereddict import OrderedDict

import shutil
from sqlalchemy import Column
import logging
from sqlalchemy import Unicode
from sqlalchemy import Integer
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, synonym

from pyramid.location import lineage
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
from mobyle2.core.utils import _, mobyle2_settings, normalizeId
from mobyle2.core.models.server import Server, ProjectServer
from mobyle2.core.models.service import Service
from mobyle2.core.models.registry import get_registry_key, set_registry_key

T, F = True, False
PUBLIC_PROJECT_NAME = 'Public project'
PUBLIC_PROJECT_USERNAME = 'Mobyle2 Public'
PROJECTS_DIR = 'mobyle2.projects_dir'


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

def projects_dir(directory=None):
    if directory is not None:
        set_registry_key(PROJECTS_DIR, directory)
    return get_registry_key(PROJECTS_DIR)

class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    description = Column(Unicode(255))
    _directory = Column('directory', Unicode(2550))
    user_id = Column(Integer, ForeignKey("users.id", "fk_project_user", use_alter=True))
    owner = relationship("User", primaryjoin="Project.user_id==User.id")
    usersroles = relationship('ProjectUserRole', backref='projets')
    groupsrolesF = relationship('ProjectGroupRole', backref='projects')
    servers = relationship('Server', backref='implied_project', secondary='projects_servers')
    services = relationship('Service', backref='implied_project')

    def object_acls(self, acls):
        for a in default_project_acls:
            self.append_acl(acls, a)

    def construct(self, commit=True):
        # !IMPORTANT! Call autolink on localhost server when we traverse /project/servers
        # link here localhost node
        localhost = Server.get_local_server()
        modified = False
        if not localhost in self.servers:
            modified = True
            self.servers.append(localhost)
        if commit and modified:
            session.add(self)
            session.commit()

    def __init__(self, name, description, owner):
        self.name = name
        self.description = description
        self.owner = owner
        self.construct(commit=False)

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

    @property
    def projects_dir(self):
        return projects_dir()

    def create_directory(self):
        p = self
        if p.id is None:
            raise Exception('Project.create: invalid project state')
        subdir = "%s" % (p.id / 1000)
        pdir = os.path.join(p.projects_dir, subdir, "%s"%p.id)
        tries = 0
        if os.path.exists(pdir):
            while tries < 10000:
                pdir = os.path.join('%s_%s' % (pdir, tries))
                if not os.path.exists(pdir):
                    break
        if not os.path.exists(pdir):
            os.makedirs(pdir)
            p._directory = pdir
            session.add(p)
            session.commit()
        else:
            raise Exception('Project directory Alrealdy exists')

    def _set_directory(self, directory):
         self._directory = directory

    def _get_directory(self):
         directory = None
         if self.id is not None:
             if self._directory is None:
                 self.create_directory()
         if self.id is not None and self._directory is None:
             raise Exception('project in  inconsistent state, no FS directory')
         else:
             directory = self._directory
         return directory

    directory = synonym('_directory', descriptor=property(_get_directory, _set_directory))

    @classmethod
    def create(cls, name=None, description=None, user=None):
        p = cls(name=name, description=description, owner=user)
        # give user the owner role
        if p is not None:
            p.make_owner(p.owner)
            p.create_directory()
        return p

    def make_owner(self, user):
        sproject = ProjectResource(self)
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

    @property
    def is_public(self):
        # leave import there for circular problems
        from mobyle2.core.models import user
        public_user = user.User.search(PUBLIC_PROJECT_USERNAME)
        return self.user.id == public_user.id

    def get_services(self, service_type=None, server=None):
        services = []
        if server is not None:
            servers = [server]
        else:
            servers = self.servers
        for s in servers:
            kw = dict(server=s, project=self)
            if service_type is not None:
                kw['type'] = service_type
                kw['enable'] = True
            svcs = self.session.query(Service).filter_by(**kw).all()
            for sv in svcs:
                if not sv in services:
                    services.append(sv)
        return services

    def get_services_by_classification(self):
        """To_implement"""
        def node(resource=None):
            return {'children': OrderedDict(),
                    "resource": resource}
        tree = node()
        raw_services = self.get_services()
        services = tree['children']['Services'] = node()
        for s in raw_services:
            if not "%ss" % s.type in services['children']:
                services['children']["%ss"%s.type] = node()
            categs = s.classification.split(':')
            data = services['children']["%ss"%s.type]
            for c in categs:
                if not c in data['children']:
                    data['children'][c] = node()
                data = data['children'][c]
            data['children'][s.name] = node(s)
	def sort_node_children(node):
	    """sort alphabetically the children of the node"""
	    unsorted_children = node['children']
	    for n,v in unsorted_children.items():
		unsorted_children[n]=sort_node_children(v)
	    sorted_children = OrderedDict(sorted(unsorted_children.items(), key=lambda t: t[0]))
	    return {'children':sorted_children,
	    'resource':node['resource']}
	tree = sort_node_children(tree)
        return services

    def get_services_by_package(self):
        """To_implement"""
        services = OrderedDict()
        raw_services = self.get_services()
        return services


class ProjectResource(SecuredObject):
    __managed_type__ = 'project'
    __managed_roles__ = default_project_roles
    __acl_groups__ = "ProjectGroupRole"
    __acl_users__ = "ProjectUserRole"
    __default_acls__  = default_project_acls
    _items = None

    @property
    def items(self):
        if not self._items:
            self._items = OrderedDict()
            try:
                self.items['servers'] = Servers(parent=self, name='servers')
            except Exception, e:
                self.logger.error('Cant load servers : %s' % e)
        return self._items

    def __init__(self, *a, **k):
        SecuredObject.__init__(self, *a, **k)
        # compatibility
        self.project = self.context


class Projects(SecuredObject):
    __default_acls__  = default_projects_acls
    __description__ = _("Projects")
    @property
    def items(self):
        default_p = Project.get_public_project()
        self._items = OrderedDict()
        for p in self.session.query(Project).all():
            if default_p == p:
                name = _('Public project')
                id = None
            else:
                name = p.name
                id = "%s" % p.id
            pr = ProjectResource(p, self, id=id, name=name)
            self._items[pr.__name__] = pr
        return self._items

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
    # imports here for circular import references
    from apex.models import create_user, AuthUser
    from mobyle2.core.models.user import User
    import transaction
    ausr = AuthUser.get_by_login(username)
    modified = False
    if ausr is None:
        kwargs = {
            'email': user_public_email,
            'username': username,
            'login': username
        }
        if registry:
            kwargs['registry'] = registry
        ausr = create_user(**kwargs)
    else:
        ausr.username = username
        ausr.email = user_public_email
        ausr.login = username
        modified = True
    # running mobyle2 __init__ recreate default project if deleted
    # only after we are sure user is created
    usr = User.by_id(ausr.id)
    if modified:
        transaction.commit()



class ServiceResource(SecuredObject):
    """."""
    def __init__(self, *a, **k):
        SecuredObject.__init__(self, *a, **k)
        self.rproject = [a for a in lineage(self) if isinstance(a, ProjectResource)][0]
        self.project = self.rproject.context
        self.service = self.context
        self.rserver =  [a for a in lineage(self) if isinstance(a, ServerResource)][0]
        self.server =  self.rserver.context


class WorkflowResource(ServiceResource):
    """."""


class ProgramResource(ServiceResource):
    """."""


class ViewerResource(ServiceResource):
    """."""


class Services(SecuredObject):
    __description__ = _('Services')
    type = None
    _items = None
    @property
    def items(self):
        tmap = {
            'workflow': WorkflowResource,
            'program': ProgramResource,
            'viewer': ViewerResource,
        }
        if not self._items:
            parent = self.__parent__
            server  = parent.context
            project  = parent.__parent__.__parent__.context
            ditems = project.get_services(server=server,service_type=self.type)
            Res = tmap.get(self.type, ServiceResource)
            self._items = OrderedDict()
            for a in ditems:
                 res = Res(a, self, name=a.name)
                 self._items[res.__name__] = res
        return self._items


class Workflows(Services):
    type = 'workflow'
    __description__ = _('Workflows')


class Programs(Services):
    type = 'program'
    __description__ = _('Programs')


class Viewers(Services):
    type = 'viewer'
    __description__ = _('Viewers')


class ServerResource(SecuredObject):
    _items = None
    @property
    def items(self):
        if not self._items:
            self._items = OrderedDict()
            try:
                self._items['services'] = Services(name='services',  parent=self)
                self._items['programs'] = Programs(name='programs',  parent=self)
                self._items['workflows'] = Workflows(name='workflows',  parent=self)
                self._items['viewers'] = Viewers(name='viewers', parent=self)
            except Exception, e:
                self.logger.error(
                    'Cant load services for : %s %s' % ( self.__name__, e))
        return self._items

class Servers(SecuredObject):
    __description__ = 'Servers'
    @property
    def items(self):
        items = OrderedDict()
        for a in self.__parent__.context.servers:
            res = ServerResource(a, self, name=a.name)
            items[res.__name__] = res
        return items

