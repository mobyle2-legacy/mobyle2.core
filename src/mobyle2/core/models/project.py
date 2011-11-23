from ordereddict import OrderedDict

from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import Integer
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from mobyle2.core.utils import _
from mobyle2.core.models import Base
import mobyle2

class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    description = Column(Unicode(255))
    user_id = Column(Integer, ForeignKey("users.id", "fk_project_user", use_alter=True))


    def __init__(self, name, description, user_id):
        self.name = name
        self.description = description
        self.user_id = user_id
        self.workflows = relationship("Workflow", backref="project")
        self.jobs = relationship("Job", backref="project")

class ProjectRessource(object):
    def __init__(self, p, parent):
        self.project = p
        self.__name__ = "%s"%p.id
        self.__parent__ = parent


class Projects:
    @property
    def items(self):
        self._items = OrderedDict([("%s"%a.id, ProjectRessource(a, self))
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

