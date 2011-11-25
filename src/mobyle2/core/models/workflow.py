from ordereddict import OrderedDict

from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import Integer
from sqlalchemy import ForeignKey

from sqlalchemy.orm import relationship
from mobyle2.core.models import Base
from mobyle2.core.utils import _

class Workflow(Base):
    __tablename__ = 'workflows'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    description = Column(Unicode(255))
    project_id = Column(Integer, ForeignKey("projects.id", name="fk_workflow_project", use_alter=True), nullable=True)
    jobs = relationship("Job", backref="workflow", uselist=True)

    def __init__(self, name, description, project=None, jobs=None):
        self.name = name
        self.description = description
        self.project = project
        if jobs is not None:
            self.jobs.extend(jobs)


