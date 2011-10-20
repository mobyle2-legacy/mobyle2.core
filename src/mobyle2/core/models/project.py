from mobyle2.core.models import Base, DBSession
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
    def __init__(self, p, n, parent):
        self.project = p
        self.__name__ = "%s"%n
        self.__parent__ = parent

class Projects(object):
    def __init__(self, request):
        self.__name__ = ''
        self.__parent__ = None
        self.request = request
        session = DBSession()
        self.projects = dict([("%s"%a.id, ProjectRessource(a, id, self)) 
                              for a in session.query(Project).all()])

    def __getitem__(self, item):
        return self.projects.get(item, None) 

def project_factory(request):
    return Projects(request)

