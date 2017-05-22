import sys
import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta
from flask import Flask, request, redirect, url_for, render_template, abort
from flask_login import LoginManager, login_user, logout_user, UserMixin, current_user, login_required
from htmlmin.main import minify

# logging.basicConfig(stream=sys.stderr)
# sys.path.insert(0, "/var/www/FlaskApp/FlaskApp/pkgs/")

from pkgs.database import DBHandler, Manager
from pkgs.utils import check_client, check_credit_card, get_my_sales

login_manager = LoginManager()

app = Flask(__name__)

login_manager.init_app(app)


class User(UserMixin):
    pass


@login_manager.user_loader
def user_loader(manager):
    db = DBHandler(manager)
    user = db.get_user(email)
    if not user:
        return
    user = User()
    user.id = email
    return user


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.xhtml')
    db = DBHandler()

    email = request.form.get('email')
    password = request.form.get('pw')
    remember = request.form.getlist('rememberMe')
    user_db = db.get_user(email)
    if user_db:
        if user_db.pw == password:
            user = User()
            user.id = email
            login_user(user, remember=bool(remember))
            return redirect(url_for('index'))
    return render_template('login.xhtml', massage='True')


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@login_manager.unauthorized_handler
def unauthorized_handler():
    return abort(401)


@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    db = DBHandler()

    user = db.get_user(current_user.id)
    return render_template('index.xhtml', user=user)


@app.route('/setting')
@login_required
def setting():
    return ''


@app.route('/my_sales')
@login_required
def my_sales():
    month = request.args.get('month')
    year = request.args.get('year')
    action = request.args.get('action')
    if not month or not str(month).isdigit() or action == 'today':
        month = datetime.today().month
    if not year or not str(year).isdigit() or action == 'today':
        year = datetime.today().year
    date_filter = datetime(int(year), int(month), 1)

    if action == 'next':
        date_filter = date_filter + relativedelta(months=1)
        month = date_filter.month
        year = date_filter.year
    if action == 'back':
        date_filter = date_filter - relativedelta(months=1)
        month = date_filter.month
        year = date_filter.year
    sales = get_my_sales(current_user.id, date_filter)
    sum_price = sum([i[0].price for i in sales])
    return render_template('my_sales.xhtml', sales=sales,
                           month=month, year=year,
                           sum_sale=len(sales), sum_price=sum_price)


@app.route('/new_connect')
@login_required
def new_connect():
    return render_template('list_company.xhtml', action='new_connect')


@app.route('/new_connect/<company>', methods=['GET', 'POST'])
@login_required
def set_company(company):
    db = DBHandler()

    tracks = db.get_all_tracks(company)
    if request.method == 'POST':

        track = request.form.get('track')
        client_id = request.form.get('client_id')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        address = request.form.get('address')
        city = request.form.get('city')
        phone = request.form.get('phone')
        email = request.form.get('email')
        sim_num = request.form.get('sim_num')
        phone_num = request.form.get('phone_num')
        credit_card = request.form.get('credit_card')
        month = request.form.get('month')
        year = request.form.get('year')
        cvv = request.form.get('cvv')
        account_num = request.form.get('account_num')
        brunch = request.form.get('brunch')
        bank = request.form.get('bank')
        errors = check_client(client_id, first_name, last_name, address, city, phone, email)
        if all([credit_card, month, year, cvv]):
            checked_credit_card = check_credit_card(credit_card, month, year, cvv)
            if not checked_credit_card:
                errors.append('כרטיס אשראי')
        if not all([credit_card, month, year, cvv]) and not all([account_num, brunch, bank]):
            errors.append('חייב למלאות כרטיס אשראי או פרטי בנק')
        if errors:
            return render_template('new_connect.xhtml',
                                   tracks=tracks,
                                   company=company,
                                   errors=errors)
        if not db.get_client(client_id):
            print('not_client')
            db.set_client(client_id, first_name, last_name, address, city, phone, email or None)
        if not db.get_credit_card(client_id):
            db.set_credit_card(client_id, credit_card, month, year, cvv, account_num, brunch, bank)
        db.set_transactions(
            current_user.id,
            db.get_track(company, track).id,
            client_id,
            credit_card,
            datetime.today(),
            sim_num,
            phone_num)
        return redirect(url_for('index'))
    track_specific = request.args.get('track_specific')
    return render_template('new_connect.xhtml', tracks=tracks, company=company, track_specific=track_specific)


@app.route('/tracks_manger')
@login_required
def tracks_manger():
    return render_template('list_company.xhtml', action='list_tracks')


@app.route('/list_tracks/<company>')
@login_required
def list_tracks(company):
    db = DBHandler()

    user = db.get_user(current_user.id)
    tracks = db.get_all_tracks(company=company)
    return render_template('list_tracks.xhtml', company=company, tracks=tracks, user=user)


@app.route('/new_track/<company>', methods=['GET', 'POST'])
@login_required
def new_track(company):
    if request.method == 'POST':
        db = DBHandler()

        user = db.get_user(current_user.id)
        if user.manager == 'True':
            price = request.form.get('price')
            name = request.form.get('name')
            description = request.form.get('description')
            db.set_track(company, price, name, description)
        return redirect(url_for('list_tracks', company=company))
    return render_template('new_track.xhtml', company=company)


@app.route('/clients')
@login_required
def clients():
    db = DBHandler()
    clients_list = db.get_all_clients()
    print(clients_list)
    return render_template('list_clients.xhtml', clients_list=clients_list, sum_clients=len(clients_list))


@app.route('/edit_client/<client_id>', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    db = DBHandler()
    client = db.get_client(client_id)
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        address = request.form.get('address')
        city = request.form.get('city')
        phone = request.form.get('phone')
        email = request.form.get('email')
        errors = check_client(client_id, first_name, last_name, address, city, phone, email)
        if errors:
            return render_template('edit_client.xhtml',
                                   client=client,
                                   errors=errors)
        db.update_client(client_id, {k: v for k, v in request.form.items()})
        return redirect(url_for('clients'))
    client = db.get_client(client_id)
    return render_template('edit_client.xhtml', client=client)


@app.route('/agents')
@login_required
def agents():
    db = DBHandler()
    agents_list = db.session.query(Manager.email, Manager.first_name, Manager.last_name).filter(
        Manager.manager == current_user.id).all()
    return render_template('list_agents.xhtml', agents_list=agents_list)


@app.route('/new_agent', methods=['GET', 'POST'])
@login_required
def new_agent():
    return render_template('new_agent.xhtml')


@app.after_request
def response_minify_js(response):
    if response.content_type == u'text/javascript':
        response.set_data(
            minify(response.get_data(as_text=True))
        )

        return response
    return response


@app.after_request
def response_minify_css(response):
    if response.content_type == u'text/css':
        response.set_data(
            minify(response.get_data(as_text=True))
        )

        return response
    return response


if __name__ == "__main__":
    app.secret_key = 'yT71682547!'
    app.run()
