import os

import logging
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Date, and_, or_, func
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


class Tags(Base):
    __tablename__ = 'Tags'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    track_id = Column(Integer, ForeignKey(Tracks.id))


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
    reminds = Column(Date)


class Forum(Base):
    __tablename__ = 'Forum'
    id = Column(Integer, primary_key=True)
    agent_id = Column(String, ForeignKey(Agents.email))
    date_time = Column(DateTime)
    massage = Column(String)


class DBGroups:
    def __init__(self, group_id):
        if not os.path.exists(LOCAL_PATH + '/data'):
            os.mkdir(LOCAL_PATH + '/data')
        self.engine = create_engine('sqlite:///{}/data/{}.db'.format(LOCAL_PATH, group_id),
                                    connect_args={'check_same_thread': False})
        self.create_all_tables()
        os.system('chown -R www-data ' + LOCAL_PATH + '/data')
        session = sessionmaker(bind=self.engine)
        self.session = session()
        self.group = group_id

    def create_all_tables(self):
        Base.metadata.create_all(self.engine, checkfirst=True)

    # Agents
    def set_agent(self, email, first_name, last_name, manager, phone=None):
        try:
            self.session.add(Agents(email=str(email).lower(),
                                    first_name=str(first_name).title(),
                                    last_name=str(last_name).title(),
                                    phone=phone,
                                    manager=manager))
            self.session.commit()
        except Exception as e:
            logging.error(e)
            self.session.rollback()

    def get_agent(self, email):
        return self.session.query(*Agents.__table__.columns).filter(Agents.email == email).first()

    def get_all_agents(self, manager=None):
        q = self.session.query(*Agents.__table__.columns)
        if manager is not None:
            q = q.filter(Agents.manager == manager)
        return q.all()

    def update_agent(self, agent_id, values):
        try:
            self.session.query(Agents).filter(Agents.email == agent_id).update(values)
            self.session.commit()
        except Exception as e:
            logging.error(e)
            self.session.rollback()

    # Tracks
    def set_track(self, company, price, name, description):
        try:
            self.session.add(Tracks(company=company,
                                    price=price,
                                    name=name,
                                    description=description))
            self.session.commit()
        except Exception as e:
            logging.error(e)
            self.session.rollback()

    def get_track(self, company=None, name=None, _id=None):
        q = self.session.query(*Tracks.__table__.columns)
        if name is not None:
            q = q.filter(Tracks.name == name)
        if company is not None:
            q = q.filter(Tracks.company == company)
        if _id is not None:
            q = q.filter(Tracks.id == _id)
        return q.first()

    def update_track(self, track_id, values):
        try:
            self.session.query(Tracks).filter(Tracks.id == track_id).update(values)
            self.session.commit()
        except Exception as e:
            logging.error(e)
            self.session.rollback()

    def get_all_tracks(self, company=None):
        q = self.session.query(*Tracks.__table__.columns)
        if company is not None:
            q = q.filter(Tracks.company == company)
        return q.all()

    # Tags
    def set_tag(self, name, track_id):
        try:
            self.session.add(Tags(name=name, track_id=track_id))
            self.session.commit()
        except Exception as e:
            logging.error(e)
            self.session.rollback()

    def get_all_tags(self, name=None, track_id=None):
        q = self.session.query(*Tags.__table__.columns)
        if name is not None:
            q = q.filter(Tags.name == name)
        if track_id is not None:
            q = q.filter(Tags.track_id == track_id)
        return q.all()

    def update_tag(self, tag_id, values):
        try:
            self.session.query(Tags).filter(Tags.id == tag_id).update(values)
            self.session.commit()
        except Exception as e:
            logging.error(e)
            self.session.rollback()

    # Clients
    def set_client(self, client_id, first_name, last_name, address, city, phone, email=None):
        try:
            self.session.add(Clients(client_id=client_id,
                                     first_name=str(first_name).title(),
                                     last_name=str(last_name).title(),
                                     address=address,
                                     city=city,
                                     phone=phone,
                                     email=str(email).lower()))
            self.session.commit()
        except Exception as e:
            logging.error(e)
            self.session.rollback()

    def get_client(self, client_id):
        return self.session.query(*Clients.__table__.columns).filter(Clients.client_id == client_id).first()

    def get_all_clients(self, by_agent=None, search=None):
        if by_agent is not None:
            q = self.session.query(Transactions, Clients).join(Clients).filter(
                Transactions.agent_id == by_agent)
            if search is not None:
                q = q.filter(or_(Clients.first_name.like('%' + search + '%'),
                                 Clients.last_name.like('%' + search + '%'),
                                 Clients.client_id.like('%' + search + '%')))
            return q.group_by(Clients.client_id).all()
        q = self.session.query(*Clients.__table__.columns)
        if search is not None:
            q = q.filter(or_(Clients.first_name.like('%' + search + '%'),
                             Clients.last_name.like('%' + search + '%'),
                             Clients.client_id.like('%' + search + '%')))
        return q.all()

    def update_client(self, client_id, values):
        try:
            self.session.query(Clients).filter(Clients.client_id == client_id).update(values)
            self.session.commit()
        except Exception as e:
            logging.error(e)
            self.session.rollback()

    # CreditCard
    def set_credit_card(self, client_id, card_number, month, year, cvv):
        try:
            self.session.add(CreditCard(client_id=client_id,
                                        card_number=card_number,
                                        month=month,
                                        year=year,
                                        cvv=cvv))
            self.session.commit()
        except Exception as e:
            logging.error(e)
            self.session.rollback()

    def get_credit_card(self, client_id):
        q = self.session.query(*CreditCard.__table__.columns).filter(CreditCard.client_id == client_id).first()
        return q

    def update_credit_card(self, _id, values):
        try:
            self.session.query(CreditCard).filter(CreditCard.id == _id).update(values)
            self.session.commit()
        except Exception as e:
            logging.error(e)
            self.session.rollback()

    # BankAccount
    def set_bank_account(self, client_id, account_num, brunch, bank_num):
        try:
            self.session.add(BankAccount(client_id=client_id,
                                         account_num=account_num,
                                         brunch=brunch,
                                         bank_num=bank_num))
            self.session.commit()
        except Exception as e:
            logging.error(e)
            self.session.rollback()

    def get_bank_account(self, client_id):
        return self.session.query(*BankAccount.__table__.columns).filter(BankAccount.client_id == client_id).first()

    # Transactions
    def set_transactions(self, agent_id, track, client_id, credit_card_id,
                         bank_account_id, date_time, sim_num, phone_num, status, comment=None, reminds=None):
        try:
            self.session.add(Transactions(agent_id=agent_id,
                                          track=track,
                                          client_id=client_id,
                                          credit_card_id=credit_card_id,
                                          bank_account_id=bank_account_id,
                                          date_time=date_time,
                                          sim_num=sim_num,
                                          phone_num=phone_num,
                                          status=status,
                                          comment=comment,
                                          reminds=reminds))
            self.session.commit()
        except Exception as e:
            logging.error(e)
            self.session.rollback()

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

    def get_transaction(self, transaction_id=None):
        q = self.session.query(*Transactions.__table__.columns)
        if transaction_id is not None:
            q = q.filter(Transactions.id == transaction_id)
        return q.first()

    def update_transactions(self, _id, values):
        try:
            self.session.query(Transactions).filter(Transactions.id == _id).update(values)
            self.session.commit()
        except Exception as e:
            logging.error(e)
            self.session.rollback()

    # Forum
    # id = Column(Integer, primary_key=True)
    # agent_id = Column(String, ForeignKey(Agents.email))
    # date_time = Column(DateTime)
    # massage = Column(String)
    def set_massage(self, agent_id, date_time, massage):
        try:
            self.session.add(Forum(agent_id=agent_id, date_time=date_time, massage=massage))
            self.session.commit()
        except Exception as e:
            logging.error(e)
            self.session.rollback()

    def get_all_massage(self, search=None):
        q = self.session.query(Forum.agent_id, Forum.date_time, Forum.massage, Agents.first_name,
                               Agents.last_name).join(Agents)
        if search is not None:
            q = q.filter(Forum.massage.like('%' + search + '%'))
        return q.order_by(Forum.date_time).all()

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
            print(_agent.first_name)
            list_agent = []
            for company in ['cellcom', 'partner', 'pelephone', '012', 'hot', 'rami_levi', 'golan']:
                tmp = [(i[1], i[2]) for i in list_db if company == i[1]]
                list_agent.append(tmp[0] if tmp else (company, 0))
            list_agent.append(('sum', sum([i[1] for i in list_agent])))
            name_agent = _agent.first_name[0] + '.' + _agent.last_name
            result[name_agent] = list_agent
        return result

    def delete_track(self, track_id):
        try:
            self.session.query(Tracks).filter(Tracks.id == track_id).delete()
            self.session.commit()
        except Exception as e:
            logging.error(e)
            self.session.rollback()

    def delete_agent(self, email):
        try:
            self.session.query(Agents).filter(Agents.email == email).delete()
            self.session.commit()
        except Exception as e:
            logging.error(e)
            self.session.rollback()

    def delete_transaction(self, _id):
        try:
            self.session.query(Transactions).filter(Transactions.id == _id).delete()
            self.session.commit()
        except Exception as e:
            logging.error(e)
            self.session.rollback()

    def delete_client(self, client_id):
        try:
            self.session.query(Clients).filter(Clients.client_id == client_id).delete()
            self.session.commit()
        except Exception as e:
            logging.error(e)
            self.session.rollback()

    def delete_credit_card(self, _id):
        try:
            self.session.query(CreditCard).filter(CreditCard.id == _id).delete()
            self.session.commit()
        except Exception as e:
            logging.error(e)
            self.session.rollback()

    def delete_bank_account(self, _id):
        try:
            self.session.query(BankAccount).filter(BankAccount.id == _id).delete()
            self.session.commit()
        except Exception as e:
            logging.error(e)
            self.session.rollback()

    def get_secure_credit_card(self, last_num):
        return self.session.query(CreditCard.card_number).filter(
            CreditCard.card_number.like('%' + last_num)).first().card_number

    # noinspection SqlNoDataSourceInspection
    def add_column(self, table, column):
        column_name = column.compile(dialect=self.engine.dialect)
        column_type = column.type.compile(self.engine.dialect)
        self.engine.execute('ALTER TABLE {} ADD COLUMN {} {}'.format(table.__tablename__, column_name, column_type))


# noinspection SpellCheckingInspection
if __name__ == '__main__':
    # db = DBGroups('yishaiphone-prodaction').add_column(Transactions, Column('reminds', Date))
    # db = DBGroups('test').add_column(Transactions, Column('reminds', Date))
    # db = DBGroups('yishaiphone-prodaction').add_column(Transactions, Column('reminds', Date))
    # db = DBGroups('yishaiphone-prodaction').delete_agent('yair.p.86@hotnail.com')
    db = DBGroups('yishaiphone-prodaction').get_reward()
    pass
