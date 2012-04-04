from sqlalchemy import Column, Unicode, Integer, ForeignKey

from mobyle2.models import Base
from mobyle2.utils import _

class JobData(Base):
    __tablename__ = 'jobsdatas'
    id = Column(Integer, primary_key=True)
    job_type = Column(Unicode(6), nullable=False)
    job_args = Column(Unicode(255))
    text_data = Column(Unicode)
    uri_file_data = Column(Unicode)
    job_id = Column(Integer,  ForeignKey("jobs.id" , "fk_jobdata_job", use_alter=True))

    def __init__(self, job_type, job_args,text_data, uri_file_data, job):
        self.job_type = job_type
        self.job_args = job_args
        self.text_data = text_data
        self.uri_file_data = uri_file_data
#        self.job_id = job_id
        self.job = job
