import re
import hashlib

import googlemaps
import pycard
from dateutil.relativedelta import relativedelta
import yagmail

from .groups_database import DBGroups, Transactions, Tracks, and_
from .users_database import DBUsers


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


def check_address(address, city):
    gmaps = googlemaps.Client('AIzaSyDv4GEWHbxhtpmMBkf4lNIP6wwi5nXwlfM')
    if gmaps.geocode('Israel, ' + city + ', ' + address) and not address.isdigit():
        return True
    return False


def check_email(email):
    return not not re.match("[^@]+@[^@]+\.[^@]+", email)


def check_client(id, first_name, last_name, address, city, phone, email):
    errors = []
    if not check_client_id(id):
        errors.append('תעודת זהות')
    if not check_first_name(first_name):
        errors.append('שם פרטי')
    if not check_last_name(last_name):
        errors.append('שם משפחה')
    if not check_address(address, city):
        errors.append('כתובת / עיר')
    if not check_phone(phone):
        errors.append('טלפון')
    if email:
        if not check_email(email):
            errors.append('אימייל')
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
               i.phone_num) for i in data]
    return result


def add_agent(group, email):
    m = hashlib.md5()
    m.update(str(group + email).encode())
    unique_id = m.hexdigest()

    db = DBUsers()
    db.set_tmp(unique_id, email, group)
    subject = 'ישיפון תקשורת - בקשה להצטרפות'
    html = '''
    <!DOCTYPE html>
    <html lang="he">
<head>
    <title></title>
</head>
<body>
    <div>
    <p>שלום %s.</h1>
    <p>ברוך הבא לישיפון-תקשורת</h3>
    <p>להשלמת תהליך ההרשמה:</p>
        <a href="http://127.0.0.1:5000/signup?secret_token=%s">לחץ כאן</button>
</div>
</body>
</html>
    ''' % (DBGroups(group).get_agent(email).first_name, str(unique_id))
    yag = yagmail.SMTP('yishaiphone@gmail.com', 'yP1q2w3e4r!')
    yag.send(to=email, subject=subject, contents=html)


def set_up_group(group, email, pw, first_name, last_name, manager=2, phone=None):
    DBGroups(group).set_agent(email, first_name, last_name, manager, phone)
    db_users = DBUsers()
    db_users.create_all_tables()
    db_users.set_user(email, pw, group)


if __name__ == '__main__':
    pass
