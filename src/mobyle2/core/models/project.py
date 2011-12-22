import os
from ordereddict import OrderedDict

import shutil
from sqlalchemy import Column
import logging
from sqlalchemy import Unicode
from sqlalchemy import Integer
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from mobyle2.core.utils import _, mobyle2_settings
from mobyle2.core.models import Base, DBSession as session
from pyramid.decorator import reify
#import mobyle2

"""
>>> from mobyle2.core.models import user,project,job,workflow
>>> from mobyle2.core.models import DBSession as session
>>> uu1 = user.AuthUser();session.add(uu1);session.commit()
>>> uu2 = user.User(uu1.id,'a');session.add(uu2);session.commit()
>>> p = project.Project("bbb", "bbb", uu2)
>>> session.add(p)
>>> session.commit()
>>> j = job.Job("bbb", "bbb", p)
>>> session.add(j)
>>> session.commit()
>>> w = workflow.Workflow("bbb", "bbb", p, [j])
>>> session.add(w)
>>> session.commit()
>>> w.programs[0] == j
True
>>> w.project == p
True

"""


class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    description = Column(Unicode(255))
    directory = Column(Unicode(2550))
    user_id = Column(Integer, ForeignKey("users.id", "fk_project_user",
                                         use_alter=True))
    #services = relationship("Service", backref="project", uselist=True)

    @classmethod
    def projects_dir(self):
        return mobyle2_settings('projects_dir')

    def __init__(self, name, description, user, directory=None, services=None):
        self.name = name
        self.description = description
        self.user = user
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

    def create_directory(self):
        p = self
        if p.id is None: 
            raise Exception('Project.create: invalid project state')
        subdir = "%s" % (p.id / 1000)
        pdir = os.path.join(Project.projects_dir(), subdir, "%s"%p.id)
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
    def create(cls, name=None, description=None, user=None, directory=None, services=None):
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
                p.create_directory()
        except Exception, e:
            if p is not None:
                # try to delete a project in an inconsistent state
                try:
                    session.delete(p)
                    session.commit()
                except Exception, e:
                    try:
                        session.rollback()
                    except Exception, e:
                        pass
            raise e     
        return p

class ProjectRessource(object):
    def __init__(self, p, parent):
        self.project = p
        self.__name__ = "%s" % p.id
        self.__parent__ = parent


class Projects:
    @property
    def items(self):
        self._items = OrderedDict([("%s" % a.id, ProjectRessource(a, self))
                                   for a in self.session.query(Project).all()])
        return self._items

    def __init__(self, name, parent):
        self.__name__ = name
        self.__parent__ = parent
        self.__description__ = _("Projects")
        self.request = parent.request
        self.session = parent.session

    def __getitem__(self, item):
        return self.items.get(item, None)


class ProjectAcl(Base):
    __tablename__ = 'acl_projects'
    rid = Column(Integer,
                 ForeignKey("projects.id",
                             name='fk_projectacl_project',
                             use_alter=True),
                 primary_key=True)
    role = Column(Integer,
                  ForeignKey("authentication_role.id",
                             name="fk_projectacl_role",
                             use_alter=True),
                  primary_key=True)
    permission = Column(Integer,
                        ForeignKey("authentication_permission.id",
                                    name="fk_projectacl_permission",
                                    use_alter=True,
                                    ondelete="CASCADE",
                                    onupdate="CASCADE"),
                        primary_key=True)
