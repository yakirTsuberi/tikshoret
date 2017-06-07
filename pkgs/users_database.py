import os

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

LOCAL_PATH = os.path.abspath(os.path.join(__file__, os.pardir))
Base = declarative_base()


class Users(Base):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    pw = Column(String)
    group = Column(String)


class Tmp(Base):
    __tablename__ = 'Tmp'
    id = Column(Integer, primary_key=True)
    unique_id = Column(String, unique=True)
    email = Column(String, unique=True)
    group = Column(String)


class DBUsers:
    def __init__(self):
        if not os.path.exists(LOCAL_PATH + '/data'):
            os.mkdir(LOCAL_PATH + '/data')
        self.engine = create_engine('sqlite:///{}/data/users.db'.format(LOCAL_PATH),
                                    connect_args={'check_same_thread': False})
        session = sessionmaker(bind=self.engine)
        self.session = session()

    def create_all_tables(self):
        Base.metadata.create_all(self.engine, checkfirst=True)
        os.system('chown -R www-data ' + LOCAL_PATH + '/data')

    def set_user(self, email, pw, group):
        self.session.add(Users(email=email, pw=pw, group=group))
        self.session.commit()

    def get_user(self, email):
        return self.session.query(*Users.__table__.columns).filter(Users.email == email).first()

    def set_tmp(self, unique_id, email, group):
        self.session.add(Tmp(unique_id=unique_id, email=email, group=group))
        self.session.commit()

    def get_tmp(self, unique_id):
        return self.session.query(*Tmp.__table__.columns).filter(Tmp.unique_id == unique_id).first()

    def delete_tmp(self, unique_id):
        self.session.query(Tmp).filter(Tmp.unique_id == unique_id).delete()
        self.session.commit()

    def update_password(self, email, pw):
        self.session.query(Users).filter(Users.email == email).update({'pw': pw})
        self.session.commit()

    def delete_user(self, email):
        self.session.query(Users).filter(Users.email == email).delete()
        self.session.commit()


if __name__ == '__main__':
    pass
