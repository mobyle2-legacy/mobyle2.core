from mobyle2.core.models import Base
from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import Integer

class Project(Base):
    __tablename__ = 'project'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    description = Column(Unicode(255))

    def __init__(self, name, description):
        self.name = name
        self.description = description

class ProjectRessource(object):
    def __init__(self, p, parent):
        self.project = p
        self.__name__ = "%s"%p.id
        self.__parent__ = parent

class Projects:
    def __init__(self, name, parent):
        self.__name__ = name
        self.__parent__ = parent
        self.request = parent.request
        self.session = parent.session
        self.items = dict([("%s"%a.id, ProjectRessource(a, self))
                              for a in self.session.query(Project).all()])

    def __getitem__(self, item):
        return self.items.get(item, None)

