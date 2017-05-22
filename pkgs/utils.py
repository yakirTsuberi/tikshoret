import re

import googlemaps
import pycard
from dateutil.relativedelta import relativedelta

from pkgs.database import DBHandler, Transactions, Tracks, and_


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


def get_my_sales(user_id, date_filter):
    db = DBHandler()
    data = db.session.query(
        *Transactions.__table__.columns).filter(
        Transactions.user_id == user_id).filter(
        and_(Transactions.date_time < date_filter + relativedelta(months=1),
             Transactions.date_time >= date_filter)
    ).all()
    result = [(db.session.query(Tracks.company, Tracks.name, Tracks.price).filter(Tracks.id == i.track).first(),
               db.get_client(i.client_id),
               i.date_time.strftime("%Y-%m-%d %H:%M %p"),
               i.sim_num,
               i.phone_num) for i in data]
    return result


if __name__ == '__main__':
    pass
