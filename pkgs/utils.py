# -*- coding: utf-8 -*-

import datetime
import random
import re
import hashlib
import string
import os
import threading
from pathlib import Path

import googlemaps
import pycard
import xlsxwriter
from dateutil.relativedelta import relativedelta
import yagmail

from groups_database import DBGroups, Transactions, Tracks, Agents, Clients, and_, or_
from users_database import DBUsers
from drive_manager.google_sheets import Sheets

LOCAL_PATH = os.path.abspath(os.path.join(__file__, os.pardir))

SIM_START_WITH = {'cellcom': '89972020', 'partner': '89972010', '012': '89972010', 'pelephone': '8997250',
                  'hot': '89972071', 'rami_levi': '89972020', 'golan': '899720800'}


def get_news():
    return open(LOCAL_PATH + '/news.txt', encoding='utf8').read().split('\n')


def set_news(news_list):
    open(LOCAL_PATH + '/news.txt', 'w', encoding='utf8').write('\n'.join(news_list))


def check_first_name(first_name):
    return 1 < len(first_name) < 12


def check_last_name(last_name):
    return 1 < len(last_name) < 12


def check_client_id(client_id):
    len_id = len(client_id)
    if len_id > 9:
        return False
    client_id = ''.join(['0' for _ in range(9 - len_id)]) + client_id
    sum_id = 0
    for item in range(len(client_id)):
        tmp = str(int(client_id[item]) * (item % 2 + 1))
        if len(tmp) > 1:
            tmp = int(tmp[0]) + int(tmp[1])
        sum_id += int(tmp)

    return sum_id % 10 == 0


def check_phone(phone: str):
    num = ['02', '03', '04', '09', '08', '05', '07']
    return phone[:2] in num and 11 > len(phone) > 7


# noinspection PyUnresolvedReferences,SpellCheckingInspection
def check_address(address, city):
    gmaps = googlemaps.Client('AIzaSyDv4GEWHbxhtpmMBkf4lNIP6wwi5nXwlfM')
    if gmaps.geocode('Israel, ' + city + ', ' + address) and not address.isdigit():
        return True
    return False


def check_email(email):
    return not not re.match("[^@]+@[^@]+\.[^@]+", email)


def check_client(_id, first_name, last_name, address, city, phone, email):
    errors = []
    if _id is not None:
        if not check_client_id(_id):
            errors.append('client_id')
    if not check_first_name(first_name):
        errors.append('first_name')
    if not check_last_name(last_name):
        errors.append('last_name')
    if not check_address(address, city):
        errors.append('address')
        errors.append('city')
    if not check_phone(phone):
        errors.append('phone')
    if email:
        if not check_email(email):
            errors.append('email')
    return errors


def check_credit_card(number, month, year, cvv):
    if not number.isdigit() or not month.isdigit() or not year.isdigit() or not cvv.isdigit():
        return False
    if int(month) > 12 or int(month) < 1 or int(year) < 1:
        return False
    if len(year) == 2:
        year = '20' + year
    card = pycard.Card(number, int(month), int(year), int(cvv))
    if len(number) >= 8:
        if card.brand == 'unknown':
            today = datetime.datetime.utcnow()
            credit_date = datetime.datetime(int(year), int(month), 1)
            return today < credit_date
        return card.is_mod10_valid and card.is_valid
    return False


def get_my_sales(group_id, agent_id, date_filter, succsess=False):
    db = DBGroups(group_id)
    data = db.session.query(
        *Transactions.__table__.columns).filter(
        Transactions.agent_id == agent_id).filter(
        and_(Transactions.date_time < date_filter + relativedelta(months=1),
             Transactions.date_time >= date_filter)
    )
    if succsess:
        data = data.filter(Transactions.status == 1)
    data = data.all()
    result = [(db.session.query(Tracks.company, Tracks.name, Tracks.price).filter(Tracks.id == item.track).first(),
               db.get_client(item.client_id),
               item.date_time.strftime("%Y-%m-%d %H:%M %p"),
               item.sim_num,
               item.phone_num,
               item.status,
               item.comment) for item in data]
    return result


def send_mail(group, email, host_url, msg='Welcome to YishaiPhone!'):
    random_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    m = hashlib.md5()
    m.update(str(random_str + group + email).encode('utf-8'))
    unique_id = m.hexdigest()

    db = DBUsers()
    db.set_tmp(unique_id, email, group)
    send_basic_mail(to=email, subject=msg, contents=host_url + '?secret_token=' + str(unique_id))


def send_basic_mail(to, subject, contents):
    def send():
        yagmail.SMTP('yishaiphone@gmail.com', 'yP1q2w3e4r!').send(to=to, subject=subject, contents=contents)

    threading.Thread(target=lambda: send()).start()


def set_up_group(group, email, pw, first_name, last_name, manager=2, phone=None):
    DBGroups(group).set_agent(email, first_name, last_name, manager, phone)
    db_users = DBUsers()
    db_users.create_all_tables()
    db_users.set_user(email, pw, group)
    _copy_tracks(group)


def sum_connections(forms):
    return len([item for item in forms if str(item).startswith('sim_num')])


def remove_user(email):
    user_db = DBUsers()
    user = user_db.get_user(email)
    agent_db = DBGroups('yishaiphone-prodaction')

    user_db.delete_user(email)
    agent_db.delete_agent(email)


def remove_full_stack_transaction(email, _id=None):
    user_db = DBUsers()
    user = user_db.get_user(email)
    db = DBGroups(user.group)
    transaction = db.session.query(Transactions)
    if _id is not None:
        transaction = transaction.filter(Transactions.id == _id)
    for t in transaction.all():
        # db.delete_credit_card(t.credit_card_id)
        # db.delete_bank_account(t.bank_account_id)
        # db.delete_client(t.client_id)
        db.delete_transaction(t.id)


def get_contents(agent_connect, form, company):
    agent = agent_connect.first_name + ' ' + agent_connect.last_name + ' ' + agent_connect.email
    client_name = form.get('first_name') + ' ' + form.get('last_name') + ' ' + form.get('email')
    client_id = form.get('client_id')
    client_phone = form.get('phone')
    client_adders = form.get('address') + ' ' + form.get('city')
    basic_sim = '<strong>סים: </strong><span>{}</span> <strong>מספר ניוד: </strong><span>{}</span><br/>'
    sims = ''.join([basic_sim.format(form.get('sim_num' + str(item)),
                                     form.get('phone_num' + str(item))) for item in range(1, sum_connections(form) + 1)]
                   )
    tran = form.get('track')
    html = open(LOCAL_PATH + '/email_syntax.html', encoding="utf8").read().format(agent, client_name, client_id,
                                                                                  client_phone, client_adders, company,
                                                                                  tran, sims)
    return html


def get_all_db():
    for item in os.listdir(LOCAL_PATH + '/data'):
        if item.endswith('.db') and item != 'users.db':
            yield DBGroups(item.replace('.db', ''))


def update_all_tracks(track_id, values):
    for db in get_all_db():
        db.update_track(track_id, values)


def set_all_tracks(company, price, name, description):
    for db in get_all_db():
        db.set_track(company, price, name, description)


# noinspection SpellCheckingInspection
def _copy_all_tracks():
    master_db = DBGroups('yishaiphone-prodaction')
    for db in get_all_db():
        if db.group != 'yishaiphone-prodaction':
            for track in master_db.get_all_tracks():
                db.set_track(*track[1:])


# noinspection SpellCheckingInspection
def _copy_tracks(group):
    master_db = DBGroups('yishaiphone-prodaction')
    db = DBGroups(group)
    for track in master_db.get_all_tracks():
        db.set_track(*track[1:])


def get_status_sales():
    for db in get_all_db():
        q = db.session.query(*Transactions.__table__.columns) \
            .filter(Transactions.status == 0) \
            .filter(or_(Transactions.reminds <= datetime.datetime.now().date(), Transactions.reminds == None)).all()
        result = []
        for k, item in enumerate(q):
            exist = False
            for t in result:
                if t['Transaction'].track == item.track and t['Transaction'].client_id == item.client_id:
                    t['sim_num'] = t['sim_num'] + (item.sim_num,)
                    t['phone_num'] = t['phone_num'] + (item.phone_num,)
                    t['len'] = [c for c in range(len(t['phone_num']))]
                    exist = True
            if not exist:
                tmp = {'Transaction': item,
                       'Track': db.get_track(_id=item.track),
                       'Client': db.get_client(item.client_id),
                       'sim_num': (item.sim_num,),
                       'phone_num': (item.phone_num,),
                       'len': [0],
                       'group': db.group}
                if item.credit_card_id:
                    tmp['CreditCard'] = db.get_credit_card(item[3])
                elif [5]:
                    tmp['BankAccount'] = db.get_bank_account(item[3])
                result.append(tmp)
        yield result


def get_later_sales():
    for db in get_all_db():
        q = db.session.query(*Transactions.__table__.columns, Agents.first_name, Agents.last_name,
                             Clients.first_name, Clients.last_name).join(Agents, Clients) \
            .filter(or_(Transactions.status == 2,
                        Transactions.reminds > datetime.datetime.now().date())).all()
        yield dict(data=q, group=db.group)


def write_to_drive(values):
    s = Sheets()
    s.write(values)


def write_to_excel(agent, date) -> Path:
    path = str(Path.home() / 'FlaskApp' / 'FlaskApp' / 'static' / 'excel_tmp' / (agent + date + '.xlsx'))
    date = date.split('-')
    date_filter = datetime.datetime(int(date[1]), int(date[0]), 1)
    workbook = xlsxwriter.Workbook(path)
    worksheet = workbook.add_worksheet()
    data = {'חברה': [], 'מסלול': [], 'לקוח': [], 'ת.ז.': [], 'טלפון': [], 'סים': [], 'תאריך': []}
    col = 0
    for i in get_my_sales('yishaiphone-prodaction', agent, date_filter, succsess=True):
        data['חברה'].append(i[0].company)
        data['מסלול'].append(i[0].name)
        data['לקוח'].append(i[1].first_name + ' ' + i[1].last_name)
        data['ת.ז.'].append(i[1].client_id)
        data['טלפון'].append(i[4])
        data['סים'].append(i[3])
        data['תאריך'].append(i[2])
    for key in data.keys():
        row = 0
        worksheet.write(row, col, key)
        for item in data[key]:
            row += 1
            worksheet.write(row, col, item)
        col += 1
    workbook.close()
    return Path(path)


# noinspection SpellCheckingInspection
if __name__ == '__main__':
    # set_up_group('yishaiphone-prodaction', 'yakir@ravtech.co.il', '71682547', 'יקיר', 'צוברי')
    remove_user('77597759gm@gmail.com')
    # remove_full_stack_transaction('yakir@ravtech.co.il', '0')
    # _copy_all_tracks()
    pass
