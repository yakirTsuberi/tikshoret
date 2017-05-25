import os

from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, and_, or_, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

LOCAL_PATH = os.path.abspath(os.path.join(__file__, os.pardir))
Base = declarative_base()


class Agents(Base):
    __tablename__ = 'Agents'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    phone = Column(String, nullable=True)
    manager = Column(Integer)  # 0=agent, 1=manger, 2=height-manager


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


class BankAccount(Base):
    __tablename__ = 'BankAccount'
    id = Column(Integer, primary_key=True)
    client_id = Column(String, ForeignKey(Clients.client_id))
    account_num = Column(String)
    brunch = Column(String)
    bank_num = Column(String)


class Transactions(Base):
    __tablename__ = 'Transactions'
    id = Column(Integer, primary_key=True)
    agent_id = Column(String, ForeignKey(Agents.email))
    track = Column(Integer, ForeignKey(Tracks.id))
    client_id = Column(String, ForeignKey(Clients.client_id))
    credit_card_id = Column(Integer, ForeignKey(CreditCard.id), nullable=True)
    bank_account_id = Column(Integer, ForeignKey(BankAccount.id), nullable=True)
    date_time = Column(DateTime)
    sim_num = Column(String)
    phone_num = Column(String)
    status = Column(Integer)  # 0=new, 1=success, 2=fail
    comment = Column(String, nullable=True)


class DBGroups:
    def __init__(self, group_id):
        if not os.path.exists(LOCAL_PATH + '/data'):
            os.mkdir(LOCAL_PATH + '/data')
        self.engine = create_engine('sqlite:///{}/data/{}.db'.format(LOCAL_PATH, group_id),
                                    connect_args={'check_same_thread': False})
        self.create_all_tables()

        session = sessionmaker(bind=self.engine)
        self.session = session()

    def create_all_tables(self):
        Base.metadata.create_all(self.engine, checkfirst=True)

    # Agents
    def set_agent(self, email, first_name, last_name, manager, phone=None):
        self.session.add(Agents(email=str(email).lower(),
                                first_name=str(first_name).title(),
                                last_name=str(last_name).title(),
                                phone=phone,
                                manager=manager))
        self.session.commit()

    def get_agent(self, email):
        return self.session.query(*Agents.__table__.columns).filter(Agents.email == email).first()

    def get_all_agents(self):
        return self.session.query(*Agents.__table__.columns).all()

    def update_agent(self, agent_id, values):
        self.session.query(Agents).filter(Agents.email == agent_id).update(values)
        self.session.commit()

    # Tracks
    def set_track(self, company, price, name, description):
        self.session.add(Tracks(company=company,
                                price=price,
                                name=name,
                                description=description))
        self.session.commit()

    def get_track(self, company=None, name=None, id=None):
        q = self.session.query(*Tracks.__table__.columns)
        if name is not None:
            q = q.filter(Tracks.name == name)
        if company is not None:
            q = q.filter(Tracks.company == company)
        if id is not None:
            q = q.filter(Tracks.id == id)
        return q.first()

    def get_all_tracks(self, company=None):
        q = self.session.query(*Tracks.__table__.columns)
        if company is not None:
            q = q.filter(Tracks.company == company)
        return q.all()

    # Clients
    def set_client(self, client_id, first_name, last_name, address, city, phone, email=None):
        self.session.add(Clients(client_id=client_id,
                                 first_name=str(first_name).title(),
                                 last_name=str(last_name).title(),
                                 address=address,
                                 city=city,
                                 phone=phone,
                                 email=str(email).lower()))
        self.session.commit()

    def get_client(self, client_id):
        return self.session.query(*Clients.__table__.columns).filter(Clients.client_id == client_id).first()

    def get_all_clients(self):
        return self.session.query(*Clients.__table__.columns).all()

    def update_client(self, client_id, values):
        self.session.query(Clients).filter(Clients.client_id == client_id).update(values)
        self.session.commit()

    # CreditCard
    def set_credit_card(self, client_id, card_number, month, year, cvv):
        self.session.add(CreditCard(client_id=client_id,
                                    card_number=card_number,
                                    month=month,
                                    year=year,
                                    cvv=cvv))
        self.session.commit()

    def get_credit_card(self, client_id):
        self.session.query(*CreditCard.__table__.columns).filter(CreditCard.client_id == client_id).first()

    # BankAccount
    def set_bank_account(self, client_id, account_num, brunch, bank_num):
        self.session.add(BankAccount(client_id=client_id,
                                     account_num=account_num,
                                     brunch=brunch,
                                     bank_num=bank_num))
        self.session.commit()

    def get_bank_account(self, client_id):
        return self.session.query(*BankAccount.__table__.columns).filter(BankAccount.client_id == client_id).first()

    # Transactions
    def set_transactions(self, agent_id, track, client_id, credit_card_id,
                         bank_account_id, date_time, sim_num, phone_num, status, comment=None):
        self.session.add(Transactions(agent_id=agent_id,
                                      track=track,
                                      client_id=client_id,
                                      credit_card_id=credit_card_id,
                                      bank_account_id=bank_account_id,
                                      date_time=date_time,
                                      sim_num=sim_num,
                                      phone_num=phone_num,
                                      status=status,
                                      comment=comment))
        self.session.commit()

    def get_all_transactions(self, agent_id=None, client_id=None, date=None, status=None):
        q = self.session.query(*Transactions.__table__.columns)
        if agent_id is not None:
            q = q.filter(Transactions.agent_id == agent_id)
        if client_id is not None:
            q = q.filter(Transactions.client_id == client_id)
        if date is not None:
            q = q.filter(
                and_(Transactions.date_time < date + relativedelta(months=1),
                     Transactions.date_time >= date))
        if status is not None:
            q = q.filter(Transactions.status == status)
        return q.all()

    def update_transactions(self, _id, values):
        self.session.query(Transactions).filter(Transactions.id == _id).update(values)
        self.session.commit()

    # Global
    def get_reward(self, date_filter=None):
        result = {}
        for _agent in self.get_all_agents():
            list_db = self.session.query(Transactions, Tracks.company, func.count()).join(Tracks).filter(
                Transactions.agent_id == _agent.email)
            if date_filter is not None:
                list_db = list_db.filter(
                    and_(Transactions.date_time < date_filter + relativedelta(months=1),
                         Transactions.date_time >= date_filter)
                )
            list_db = list_db.group_by(Tracks.company).all()
            list_agent = []
            for company in ['cellcom', 'partner', 'pelephone', '012', 'hot']:
                tmp = [(i[1], i[2]) for i in list_db if company == i[1]]
                list_agent.append(tmp[0] if tmp else (company, 0))
            list_agent.append(('sum', sum([i[1] for i in list_agent])))
            name_agent = _agent.first_name[0] + '.' + _agent.last_name
            result[name_agent] = list_agent
        return result

    def get_status_sales(self):
        q = self.session.query(*Transactions.__table__.columns) \
            .filter(or_(Transactions.status == 0, Transactions.status == 2)).all()
        result = []
        for k, i in enumerate(q):
            tmp = {'Transaction': i}
            tmp['Track'] = self.get_track(id=i.track)
            tmp['Client'] = self.get_client(i.client_id)
            if i[4]:
                tmp['CreditCard'] = self.get_credit_card(i[3])
            elif [5]:
                tmp['BankAccount'] = self.get_bank_account(i[3])
            result.append(tmp)
        return result


if __name__ == '__main__':
    pass
