from datetime import datetime

from sqlalchemy import Column, Unicode, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from mobyle2.models import Base
from mobyle2.utils import _

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    host = Column(Unicode(255))
    submit_date = Column(DateTime(), default=datetime.now())
    status = Column(Unicode)
    last_status_message = Column(Unicode)
    project_id = Column(Integer,  ForeignKey("projects.id" , "fk_job_proijec", use_alter=True),  nullable=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id", "fk_job_workflow", use_alter=True), nullable=True)
    jobs_data = relationship("JobData", backref="job", uselist=True)

    def __init__(self, name, host, project=None, workflow=None, jobs_data=None):
        self.name = name
        self.host = host
        self.project = project
        self.workflow = workflow
        if jobs_data is not None:
            self.jobs_data.extend(jobs_data)

    def get_status(self):
        """Read status from xml file."""
        if self.status != 'Done':
            self.status = self.get_job_satus()
            self.last_status_message = self.get_last_job_satus_message()
        return self.status

    def get_job_satus(self):
        """Get status from xml_file."""
        return u'readed from xml file'

    def get_last_job_satus_message(self):
        """Get last status message from xml_file."""
        return u'last message readed from xml file'
