from ordereddict import OrderedDict

from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import Integer
from sqlalchemy import ForeignKey

from mobyle2.core.models import Base
from mobyle2.core.utils import _

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    description = Column(Unicode(255))
    project_id = Column(Integer,  ForeignKey("projects.id" , "fk_job_proijec", use_alter=True),  nullable=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id", "fk_job_workflow", use_alter=True), nullable=True)

    def __init__(self, name, description, project_id=None, workflow_id=None):
        self.name = name
        self.description = description
        self.project_id = project_id
        self.workflow_id = workflow_id



