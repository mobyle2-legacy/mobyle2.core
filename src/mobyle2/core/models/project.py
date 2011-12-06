from ordereddict import OrderedDict

from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import Integer
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from mobyle2.core.utils import _
from mobyle2.core.models import Base
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
    user_id = Column(Integer, ForeignKey("users.id", "fk_project_user",
                                         use_alter=True))
    workflows = relationship("Workflow", backref="project", uselist=True)
#    jobs = relationship("Job", backref="project", uselist=True)
    programs = relationship("Program", backref="project", uselist=True)

    def __init__(self, name, description, user, workflows=None, programs=None):
        self.name = name
        self.description = description
        self.user = user
        if programs is not None:
            self.programs.extend(programs)
        if workflows is not None:
            self.workflows.extend(workflows)


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
