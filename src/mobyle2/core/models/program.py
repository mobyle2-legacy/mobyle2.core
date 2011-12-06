from sqlalchemy import Column, Unicode, Integer, ForeignKey, DateTime

from mobyle2.core.models import Base
from mobyle2.core.utils import _


class Program(Base):
    __tablename__ = 'programs'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
#    project_id = Column(Integer,  ForeignKey("projects.id" , "fk_job_proijec", use_alter=True),  nullable=True)
    project_id = Column(Integer,
                        ForeignKey("projects.id",
                                   "fk_program_project",
                                   use_alter=True),
                        nullable=True)
#    workflow_id = Column(Integer, ForeignKey("workflows.id", "fk_job_workflow", use_alter=True), nullable=True)
    workflow_id = Column(Integer,
                         ForeignKey("workflows.id",
                                    "fk_program_workflow",
                                    use_alter=True),
                         nullable=True)

    def __init__(self, name, host, project=None, workflow=None):
        self.name = name
        self.host = host
        self.project = project
        self.workflow = workflow
