from ordereddict import OrderedDict

from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import Integer
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from mobyle2.core.models.base import Base
from mobyle2.core.utils import _

from mobyle2.core.models import workflow, project

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    description = Column(Unicode(255))
    project_id = Column(Integer,  ForeignKey(project.Project.id),   nullable=True)
    workflow_id = Column(Integer, ForeignKey(workflow.Workflow.id), nullable=True)

    def __init__(self, name, description, project_id=None, workflow_id=None):
        self.name = name
        self.description = description
        self.project_id = project_id
        self.workflow_id = workflow_id
        self.workflow = relationship(workflow.Workflow, backref="jobs")
        self.project = relationship(project.Project, backref="jobs")


