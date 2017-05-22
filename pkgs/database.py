import os

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, DateTime, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

LOCAL_PATH = os.path.abspath(os.path.join(__file__, os.pardir))
Base = declarative_base()


class Manager(Base):
    __tablename__ = 'Manager'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    pw = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    phone = Column(String, nullable=True)


class Agents(Base):
    __tablename__ = 'Agents'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    pw = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    phone = Column(String, nullable=True)
    first_time = Column(Boolean)


class Tracks(Base):
    __tablename__ = 'Tracks'
    id = Column(Integer, primary_key=True)
    company = Column(String)
    price = Column(Float)
    name = Column(String)
    description = Column(String)


class Clients(Base):
    __tablename__ = 'Clients'
    id = Column(Integer, primary_key=True)
    client_id = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    address = Column(String)
    city = Column(String)
    phone = Column(String)
    email = Column(String, nullable=True)


class CreditCard(Base):
    __tablename__ = 'CreditCard'
    id = Column(Integer, primary_key=True)
    client_id = Column(String, ForeignKey(Clients.client_id))
    card_number = Column(String, unique=True)
    month = Column(String)
    year = Column(String)
    cvv = Column(String)
    account_num = Column(String)
    brunch = Column(String)
    bank = Column(String)


class Transactions(Base):
    __tablename__ = 'Transactions'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey(Manager.email))
    track = Column(String, ForeignKey(Tracks.id))
    client_id = Column(String, ForeignKey(Clients.client_id))
    agent = Column(String, ForeignKey(Agents.email))
    credit_card_id = Column(String, ForeignKey(CreditCard.id), nullable=True)
    date_time = Column(DateTime)
    sim_num = Column(String)
    phone_num = Column(String)
    status = Column(Boolean)
    comment = Column(String)


class DBHandler:
    def __init__(self, user_id):
        self.engine = create_engine('sqlite:///{}/databases/{}.db'.format(LOCAL_PATH, user_id),
                                    connect_args={'check_same_thread': False})

        session = sessionmaker(bind=self.engine)
        self.session = session()

    def create_all_tables(self):
        Base.metadata.create_all(self.engine, checkfirst=True)

    # Users
    def get_all_users(self):
        return self.session.query(*Manager.__table__.columns).all()

    def get_user(self, email):
        return self.session.query(*Manager.__table__.columns).filter(Manager.email == email).first()

    def set_user(self, email, pw, first_name, last_name, manager):
        self.session.add(Manager(email=email,
                                 pw=pw,
                                 first_name=first_name,
                                 last_name=last_name,
                                 manager=manager))
        try:
            self.session.commit()
        except:
            self.session.rollback()

    # Agents
    def get_all_agents(self, manager):
        return self.session.query(
            *Agents.__table__.columns).filter(Agents.manager == manager).all()

    def set_agent(self, email, pw, first_name, last_name, manager):
        self.session.add(Agents(email=email,
                                pw=pw,
                                first_name=first_name,
                                last_name=last_name,
                                manager=manager))
        try:
            self.session.commit()
        except:
            self.session.rollback()

    # Tacks
    def get_all_tracks(self, company=None):
        result = self.session.query(*Tracks.__table__.columns)
        if company is not None:
            result = result.filter(Tracks.company == company)
        return result.all()

    def get_track(self, company, name):
        return self.session.query(*Tracks.__table__.columns).filter(Tracks.company == company).filter(
            Tracks.name == name).first()

    def set_track(self, company, price, name, description):
        self.session.add(Tracks(company=company,
                                price=price,
                                name=name,
                                description=description))
        try:
            self.session.commit()
        except:
            self.session.rollback()

    # Clients
    def get_all_clients(self):
        result = self.session.query(*Clients.__table__.columns)
        return result.all()

    def get_client(self, client_id):
        return self.session.query(*Clients.__table__.columns).filter(Clients.client_id == client_id).first()

    def set_client(self, client_id, first_name, last_name, address, city, phone, email=None):
        self.session.add(Clients(client_id=client_id,
                                 first_name=first_name,
                                 last_name=last_name,
                                 address=address,
                                 city=city,
                                 phone=phone,
                                 email=email
                                 ))
        try:
            print('set_client')
            self.session.commit()
        except Exception as e:
            print('error_set_client', e)

            self.session.rollback()

    def update_client(self, client_id, form):
        self.session.query(Clients).filter(Clients.client_id == client_id).update(form)
        self.session.commit()

    # CreditCard
    def get_credit_card(self, client_id):
        result = self.session.query(*CreditCard.__table__.columns).filter(CreditCard.client_id == client_id)
        return result.first()

    def set_credit_card(self, client_id, card_number, month, year, cvv, account_num, brunch, bank):
        self.session.add(CreditCard(client_id=client_id,
                                    card_number=card_number,
                                    month=month,
                                    year=year,
                                    cvv=cvv,
                                    account_num=account_num,
                                    brunch=brunch,
                                    bank=bank
                                    ))
        try:
            self.session.commit()
        except:
            self.session.rollback()

    # Transactions
    def get_transactions(self, user_id):
        result = self.session.query(*Transactions.__table__.columns).filter(Transactions.user_id == user_id)
        return result.first()

    def get_all_transactions(self):
        return self.session.query(*Transactions.__table__.columns).all()

    def set_transactions(self, user_id, track, client_id, credit_card_id, date_time, sim_num, phone_num, status=None,
                         comment=None):
        self.session.add(Transactions(user_id=user_id,
                                      track=track,
                                      client_id=client_id,
                                      credit_card_id=credit_card_id,
                                      date_time=date_time,
                                      sim_num=sim_num,
                                      phone_num=phone_num,
                                      status=status,
                                      comment=comment
                                      ))
        try:
            self.session.commit()
        except:
            self.session.rollback()


if __name__ == '__main__':
    db = DBHandler('yakir@ravtech.co.il')
    db.create_all_tables()
