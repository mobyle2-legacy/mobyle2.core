from mobyle2.core.models import Base, DBSession
from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import Integer


from cryptacular.bcrypt import BCRYPTPasswordManager
crypt = BCRYPTPasswordManager()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    userid = Column(Unicode(20))
    password = Column(Unicode(20))
    fullname = Column(Unicode(40))
    about = Column(Unicode(255))

    def __init__(self, userid, password, fullname, about):
        self.userid = userid
        self.password = crypt.encode(password)
        self.fullname = fullname
        self.about = about

def check_login(login, password):
    session = DBSession()
    user = session.query(User).filter_by(userid=login).first()
    if user is not None:
        hashed_password = user.password
        if crypt.check(hashed_password, password):
            return True
    return False
