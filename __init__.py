import sys
import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta
from flask import Flask, request, redirect, url_for, render_template, abort
from flask_login import LoginManager, login_user, logout_user, UserMixin, current_user, login_required
from flask.ext.cache import Cache
from htmlmin.main import minify

logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, "/var/www/FlaskApp/FlaskApp/pkgs/")

from .pkgs.groups_database import DBGroups
from .pkgs.users_database import DBUsers
from .pkgs.utils import check_client, check_credit_card, get_my_sales, add_agent, sum_connections

login_manager = LoginManager()

app = Flask(__name__)

login_manager.init_app(app)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})


class User(UserMixin):
    pass


@login_manager.user_loader
def user_loader(email):
    db = DBUsers()
    user_db = db.get_user(email)
    if not user_db:
        return
    user = User()
    user.id = user_db.email
    user.group = user_db.group
    return user


@app.route('/login', methods=['GET', 'POST'])
@cache.cached(60)
def login():
    if request.method == 'GET':
        return render_template('login.xhtml')
    db = DBUsers()
    email = request.form.get('email')
    password = request.form.get('pw')
    remember = request.form.getlist('rememberMe')
    user_db = db.get_user(email)
    if user_db:
        if user_db.pw == password:
            user = User()
            user.id = email
            user.group = user_db.group
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


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    db = DBUsers()
    if request.method == 'POST':
        pw = request.form.get('pw')
        re_pw = request.form.get('re_pw')
        unique_id = request.form.get('secret_token')
        user = db.get_tmp(unique_id)
        if pw != re_pw:
            return render_template('signup.xhtml', massage='הסיסמאות אינן תואמות.', secret_token=unique_id)
        db.set_user(user.email, pw, user.group)
        db.delete_tmp(unique_id)
        return redirect(url_for('index'))
    unique_id = request.args.get('secret_token')
    user = db.get_tmp(unique_id)
    if not user:
        return 'Bad Request', 401

    return render_template('signup.xhtml', secret_token=unique_id)


@app.route('/')
@cache.cached(60)
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    db = DBGroups(current_user.group)
    user = db.get_agent(current_user.id)
    return render_template('index.xhtml', user=user)


@app.route('/setting')
@login_required
def setting():
    return ''


@app.route('/my_sales')
@login_required
def my_sales():
    db = DBGroups(current_user.group)
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
    sales = get_my_sales(current_user.group, current_user.id, date_filter)
    sum_price = sum([i[0].price for i in sales])
    return render_template('my_sales.xhtml', sales=sales,
                           month=month, year=year,
                           sum_sale=len(sales), sum_price=sum_price)


@app.route('/new_connect')
@login_required
@cache.cached(60)
def new_connect():
    return render_template('list_company.xhtml', action='new_connect')


@app.route('/new_connect/<company>', methods=['GET', 'POST'])
@login_required
@cache.cached(60)
def set_company(company):
    db = DBGroups(current_user.group)

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

        # sim_num = request.form.get('sim_num')
        # phone_num = request.form.get('phone_num')

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
        for i in range(1, sum_connections(request.form)):
            if not db.get_client(client_id):
                db.set_client(client_id, first_name, last_name, address, city, phone, email or None)
            if credit_card:
                if not db.get_credit_card(client_id):
                    db.set_credit_card(client_id, credit_card, month, year, cvv)
            if account_num:
                if not db.get_bank_account(client_id):
                    db.set_bank_account(client_id, account_num, brunch, bank)
            db.set_transactions(
                current_user.id,
                db.get_track(company=company, name=track).id,
                client_id,
                credit_card,
                db.get_bank_account(client_id).id,
                datetime.today(),
                request.form.get('sim_num' + str(i)),
                request.form.get('phone_num' + str(i)),
                0)
        return redirect(url_for('index'))
    track_specific = request.args.get('track_specific')
    return render_template('new_connect.xhtml', tracks=tracks, company=company, track_specific=track_specific)


@app.route('/tracks_manger')
@login_required
@cache.cached(60)
def tracks_manger():
    return render_template('list_company.xhtml', action='list_tracks')


@app.route('/list_tracks/<company>')
@login_required
def list_tracks(company):
    db = DBGroups(current_user.group)

    agent = db.get_agent(current_user.id)
    tracks = db.get_all_tracks(company=company)
    return render_template('list_tracks.xhtml', company=company, tracks=tracks, user=agent)


@app.route('/new_track/<company>', methods=['GET', 'POST'])
@login_required
@cache.cached(60)
def new_track(company):
    if request.method == 'POST':
        db = DBGroups(current_user.group)

        agent = db.get_agent(current_user.id)
        if agent.manager > 1:
            price = request.form.get('price')
            name = request.form.get('name')
            description = request.form.get('description')
            db.set_track(company, price, name, description)
        return redirect(url_for('list_tracks', company=company))
    return render_template('new_track.xhtml', company=company)


@app.route('/clients')
@login_required
def clients():
    db = DBGroups(current_user.group)
    clients_list = db.get_all_clients()
    return render_template('list_clients.xhtml', clients_list=clients_list, sum_clients=len(clients_list))


@app.route('/edit_client/<client_id>', methods=['GET', 'POST'])
@login_required
@cache.cached(60)
def edit_client(client_id):
    db = DBGroups(current_user.group)
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
    db = DBGroups(current_user.group)
    if db.get_agent(current_user.id).manager < 2:
        return 'Not Found', 404
    agents_list = db.get_all_agents()
    return render_template('list_agents.xhtml', agents_list=agents_list)


@app.route('/new_agent', methods=['GET', 'POST'])
@login_required
@cache.cached(60)
def new_agent():
    db = DBGroups(current_user.group)
    if db.get_agent(current_user.id).manager < 2:
        return 'Not Found', 404
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        manager = request.form.get('manager')
        phone = request.form.get('phone')
        db.set_agent(email=email, first_name=first_name, last_name=last_name, manager=manager, phone=phone or None)
        add_agent(current_user.group, email, request.host_url)
        return redirect(url_for('agents'))
    return render_template('new_agent.xhtml')


@app.route('/edit_agent/<agent_id>', methods=['GET', 'POST'])
@login_required
@cache.cached(60)
def edit_agent(agent_id):
    db = DBGroups(current_user.group)
    if db.get_agent(current_user.id).manager < 2:
        return 'Not Found', 404
    agent = db.get_agent(agent_id)
    if request.method == 'POST':
        db.update_agent(agent_id, {k: v for k, v in request.form.items()})
        return redirect(url_for('agents'))
    return render_template('edit_agent.xhtml', agent=agent)


@app.route('/reward_and_expectation')
@login_required
def reward_and_expectation():
    db = DBGroups(current_user.group)
    if db.get_agent(current_user.id).manager < 2:
        return 'Not Found', 404
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
    data = db.get_reward(date_filter)
    return render_template('reward_and_expectation.xhtml', month=month, year=year, data=data)


@app.route('/status_sales', methods=['GET', 'POST'])
@login_required
def status_sales():
    db = DBGroups(current_user.group)
    if db.get_agent(current_user.id).manager < 1:
        return 'Not Found', 404
    if request.method == 'POST':
        status = request.form.get('status')
        comment = request.form.get('comment')
        tran_id = request.form.get('tran_id')
        db.update_transactions(tran_id, {'status': int(status),
                                         'comment': comment})
    sales = db.get_status_sales()
    return render_template('status_sales.xhtml', sales=sales)


@app.after_request
def response_minify_js(response):
    if response.content_type == u'text/javascript':
        response.set_data(
            minify(response.get_data(as_text=True)))
        return response
    return response


@app.after_request
def response_minify_css(response):
    if response.content_type == u'text/css':
        response.set_data(
            minify(response.get_data(as_text=True)))
        return response
    return response


if __name__ == "__main__":
    app.secret_key = 'yT71682547!'
    app.run()
