import os

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

LOCAL_PATH = os.path.abspath(os.path.join(__file__, os.pardir))
Base = declarative_base()


class Users(Base):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True)
    email = Column(String)
    pw = Column(String)
    group = Column(String)


class Tmp(Base):
    __tablename__ = 'Tmp'
    id = Column(Integer, primary_key=True)
    unique_id = Column(String, unique=True)
    email = Column(String)
    group = Column(String)


class DBUsers:
    def __init__(self, name='users'):
        if not os.path.exists(LOCAL_PATH + '/data'):
            os.mkdir(LOCAL_PATH + '/data')
        self.engine = create_engine('sqlite:///{}/data/{}.db'.format(LOCAL_PATH, name),
                                    connect_args={'check_same_thread': False})
        session = sessionmaker(bind=self.engine)
        self.session = session()

    def create_all_tables(self):
        Base.metadata.create_all(self.engine, checkfirst=True)
        os.system('chown -R www-data ' + LOCAL_PATH + '/data')

    def set_user(self, email, pw, group):
        self.session.add(Users(email=email, pw=pw, group=group))
        self.session.commit()

    def get_user(self, email=None, id=None):
        if email is not None:
            return self.session.query(*Users.__table__.columns).filter(Users.email == email).first()
        if id is not None:
            return self.session.query(*Users.__table__.columns).filter(Users.id == id).first()

    def get_all_users(self, email=None):
        q = self.session.query(*Users.__table__.columns)
        if email is not None:
            q = q.filter(Users.email == email)
        return q.all()

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


def copy_db():
    db1 = DBUsers()
    db2 = DBUsers('users_tmp')
    db2.create_all_tables()
    for user in db1.session.query(*Users.__table__.columns).all():
        db2.set_user(*user[1:])
    for tmp in db1.session.query(*Tmp.__table__.columns).all():
        db2.set_user(*tmp[1:])
    db1.session.close()
    db2.session.close()
    data_path = LOCAL_PATH + '/data'
    os.remove(data_path + '/users.db')
    os.renames(data_path + '/users_tmp.db', data_path + '/users.db')


if __name__ == '__main__':
    copy_db()
