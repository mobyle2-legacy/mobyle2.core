from mobyle2.core.models import Base, DBSession
from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import Integer


from cryptacular.bcrypt import BCRYPTPasswordManager


crypt = BCRYPTPasswordManager()

user_statuses = {
    'p' : 'Pending',
    'a' : 'Active',
    's' : 'Suspended',
}

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    userid = Column(Unicode(20))
    email = Column(Unicode(50))
    password = Column(Unicode(255))
    fullname = Column(Unicode(40))
    about = Column(Unicode(255))
    status = Column(Unicode(1))

    def __init__(self, userid, email, password, fullname, about, status):
        self.userid = userid
        self.email = email
        self.password = crypt.encode(password)
        self.fullname = fullname
        self.about = about
        self.status = status

    def get_status(self):
        user_statuses.get(self.status, None)

def check_login(login, password):
    session = DBSession()
    user = session.query(User).filter_by(userid=login).first()
    if user is not None:
        hashed_password = user.password
        if crypt.check(hashed_password, password):
            return True
    return False
