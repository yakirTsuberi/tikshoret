import random
import re
import hashlib
import string

import googlemaps
import pycard
from dateutil.relativedelta import relativedelta
import yagmail

from groups_database import DBGroups, Transactions, Tracks, and_
from users_database import DBUsers

SIM_START_WITH = {'cellcom': '89972020', 'partner': '89972010', '012': '89972010', 'pelephone': '8997250',
                  'hot': '89972071'}

YAG = yagmail.SMTP('yishaiphone@gmail.com', 'yP1q2w3e4r!')

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
    for i in range(len(client_id)):
        tmp = str(int(client_id[i]) * (i % 2 + 1))
        if len(tmp) > 1:
            tmp = int(tmp[0]) + int(tmp[1])
        sum_id += int(tmp)

    return sum_id % 10 == 0


def check_phone(phone: str):
    num = ['02', '03', '04', '09', '08', '05', '07']
    return phone[:2] in num and 11 > len(phone) > 7


# noinspection PyUnresolvedReferences
def check_address(address, city):
    gmaps = googlemaps.Client('AIzaSyDv4GEWHbxhtpmMBkf4lNIP6wwi5nXwlfM')
    if gmaps.geocode('Israel, ' + city + ', ' + address) and not address.isdigit():
        return True
    return False


def check_email(email):
    return not not re.match("[^@]+@[^@]+\.[^@]+", email)


def check_client(_id, first_name, last_name, address, city, phone, email):
    errors = []
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
    card = pycard.Card(number, int(month), int(year), cvv)
    return card.is_mod10_valid and card.is_expired


def get_my_sales(group_id, agent_id, date_filter):
    db = DBGroups(group_id)
    data = db.session.query(
        *Transactions.__table__.columns).filter(
        Transactions.agent_id == agent_id).filter(
        and_(Transactions.date_time < date_filter + relativedelta(months=1),
             Transactions.date_time >= date_filter)
    ).all()
    result = [(db.session.query(Tracks.company, Tracks.name, Tracks.price).filter(Tracks.id == i.track).first(),
               db.get_client(i.client_id),
               i.date_time.strftime("%Y-%m-%d %H:%M %p"),
               i.sim_num,
               i.phone_num,
               i.status,
               i.comment) for i in data]
    return result


def send_mail(group, email, host_url, msg='Welcome to YishaiPhone!'):
    random_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    m = hashlib.md5()
    m.update(str(random_str + group + email).encode('utf-8'))
    unique_id = m.hexdigest()

    db = DBUsers()
    db.set_tmp(unique_id, email, group)

    YAG.send(to=email, subject=msg,
             contents=host_url + '?secret_token=' + str(unique_id))


def set_up_group(group, email, pw, first_name, last_name, manager=2, phone=None):
    DBGroups(group).set_agent(email, first_name, last_name, manager, phone)
    db_users = DBUsers()
    db_users.create_all_tables()
    db_users.set_user(email, pw, group)


def sum_connections(forms):
    return len([i for i in forms if str(i).startswith('sim_num')])


def remove_user(email):
    user_db = DBUsers()
    user = user_db.get_user(email)
    agent_db = DBGroups(user.group)

    agent_db.delete_agent(email)
    user_db.delete_user(email)


def remove_full_stack_transaction(email, _id=None):
    user_db = DBUsers()
    user = user_db.get_user(email)
    db = DBGroups(user.group)
    transaction = db.session.query(Transactions)
    ta = transaction.all()
    print([(i.id, i.client_id) for i in ta])
    if _id is not None:
        transaction = transaction.filter(Transactions.id == _id)
    for t in transaction.all():
        db.delete_credit_card(t.credit_card_id)
        db.delete_bank_account(t.bank_account_id)
        db.delete_client(t.client_id)
        db.delete_transaction(t.id)


if __name__ == '__main__':
    # set_up_group('test', 'yakir@ravtech.co.il', '71682547', 'יקיר', 'צוברי')
    # remove_user('tsuberyr@gmail.com')
    # remove_full_stack_transaction('yakir@ravtech.co.il', 0)
    pass
