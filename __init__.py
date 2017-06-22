import sys
import logging
import datetime

from dateutil.relativedelta import relativedelta
from flask import Flask, request, redirect, url_for, render_template, abort
from flask_login import LoginManager, login_user, logout_user, UserMixin, current_user, login_required
from htmlmin.main import minify

logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, "/var/www/FlaskApp/FlaskApp/pkgs/")

from .pkgs.groups_database import DBGroups
from .pkgs.users_database import DBUsers
from .pkgs.utils import check_client, check_credit_card, get_my_sales, send_mail, sum_connections, SIM_START_WITH, \
    get_news, set_news, remove_full_stack_transaction, send_basic_mail

login_manager = LoginManager()

app = Flask(__name__)

login_manager.init_app(app)


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
        tmp_user = db.get_tmp(unique_id)
        if pw != re_pw:
            return render_template('signup.xhtml', massage='הסיסמאות אינן תואמות.', secret_token=unique_id)
        db.set_user(tmp_user.email, pw, tmp_user.group)
        db.delete_tmp(unique_id)

        user_db = db.get_user(tmp_user.email)
        user = User()
        user.id = tmp_user.email
        user.group = user_db.group
        login_user(user)

        return redirect(url_for('index'))
    unique_id = request.args.get('secret_token')
    tmp_user = db.get_tmp(unique_id)
    if not tmp_user:
        return 'Bad Request', 401

    return render_template('signup.xhtml', secret_token=unique_id)


@app.route('/update_password', methods=['GET', 'POST'])
def update_password():
    db = DBUsers()
    if request.method == 'POST':
        pw = request.form.get('pw')
        re_pw = request.form.get('re_pw')
        unique_id = request.form.get('secret_token')
        tmp_user = db.get_tmp(unique_id)
        if pw != re_pw:
            return render_template('update_password.xhtml', massage='הסיסמאות אינן תואמות.', secret_token=unique_id)
        db.update_password(tmp_user.email, pw)
        db.delete_tmp(unique_id)
        return redirect(url_for('index'))
    unique_id = request.args.get('secret_token')
    tmp_user = db.get_tmp(unique_id)
    if not tmp_user:
        return 'Bad Request', 401

    return render_template('update_password.xhtml', secret_token=unique_id)


@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    db = DBGroups(current_user.group)
    user = db.get_agent(current_user.id)
    return render_template('index.xhtml', user=user, news=get_news())


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
        month = datetime.datetime.today().month
    if not year or not str(year).isdigit() or action == 'today':
        year = datetime.datetime.today().year
    date_filter = datetime.datetime(int(year), int(month), 1)

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
def new_connect():
    return render_template('list_company.xhtml', action='new_connect')


@app.route('/new_connect/<company>', methods=['GET', 'POST'])
@login_required
def set_company(company):
    db = DBGroups(current_user.group)
    all_c = db.get_all_clients()
    clients_list = []
    for c in all_c:
        ba = db.get_bank_account(c.client_id) or []
        cc = db.get_credit_card(c.client_id) or []
        if cc:
            tmp = []
            for k, v in enumerate(cc):
                if k == 2:
                    tmp.append(v[-4:].rjust(len(v), "*"))
                else:
                    tmp.append(v)
            cc = tmp
        clients_list.append([c, ba, cc])
    tracks = db.get_all_tracks(company)
    if request.method == 'POST':

        track = request.form.get('track')

        # Client
        client_id = request.form.get('client_id')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        address = request.form.get('address')
        city = request.form.get('city')
        phone = request.form.get('phone')
        email = request.form.get('email')

        # CreditCard
        credit_card = request.form.get('credit_card')
        month = request.form.get('month')
        year = request.form.get('year')
        cvv = request.form.get('cvv')

        # BankAccount
        account_num = request.form.get('account_num')
        brunch = request.form.get('brunch')
        bank = request.form.get('bank')

        # Check Client
        errors = check_client(client_id, first_name, last_name, address, city, phone, email)

        # Check CreditCard
        if all([credit_card, month, year, cvv]):
            if '*' in credit_card:
                credit_card = db.get_secure_credit_card(credit_card[-4:])
            checked_credit_card = check_credit_card(credit_card, month, year, cvv)
            if not checked_credit_card:
                errors.append('credit_card')
        if not all([credit_card, month, year, cvv]) and not all([account_num, brunch, bank]):
            errors.append('credit_card')
            errors.append('bank')

        if errors:
            tmp = {k: v for k, v in request.form.items() if k != 'credit_card'}
            return render_template('new_connect.xhtml',
                                   tracks=tracks,
                                   company=company,
                                   errors=errors,
                                   data=tmp,
                                   start_sim=SIM_START_WITH.get(company),
                                   clients=clients_list)

        credit_card_id = None
        account_num_id = None
        for i in range(1, sum_connections(request.form) + 1):
            if not db.get_client(client_id):
                db.set_client(client_id, first_name, last_name, address, city, phone, email or None)
            if credit_card:
                if not db.get_credit_card(client_id):
                    db.set_credit_card(client_id, credit_card, month, year, cvv)
                credit_card_id = db.get_credit_card(client_id).id
            if account_num:
                if not db.get_bank_account(client_id):
                    db.set_bank_account(client_id, account_num, brunch, bank)
                account_num_id = db.get_bank_account(client_id).id
            db.set_transactions(
                current_user.id,
                db.get_track(company=company, name=track).id,
                client_id,
                credit_card_id,
                account_num_id,
                datetime.datetime.today(),
                request.form.get('sim_num' + str(i)),
                request.form.get('phone_num' + str(i)),
                0)
        for agent in db.get_all_agents(manager=2):
            c = 'Agent: ' + current_user.id
            k = 'Client: ' + client_id
            send_basic_mail(to=agent.email, subject='New Connect', contents=c + '\n' + k)
        return redirect(url_for('index'))
    track_specific = request.args.get('track_specific')
    return render_template('new_connect.xhtml', tracks=tracks, company=company, track_specific=track_specific,
                           start_sim=SIM_START_WITH.get(company), data={}, clients=clients_list)


@app.route('/tracks_manger')
@login_required
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


@app.route('/edit_track/<track_id>', methods=['GET', 'POST'])
@login_required
def edit_track(track_id):
    db = DBGroups(current_user.group)
    track = db.get_track(_id=track_id)
    if request.method == 'POST':
        agent = db.get_agent(current_user.id)
        if agent.manager > 1:
            db.update_track(track_id, {k: v for k, v in request.form.items()})
        return redirect(url_for('list_tracks', company=track.company))
    return render_template('edit_track.xhtml', track=track)


@app.route('/delete_track/<track_id>')
@login_required
def delete_track(track_id):
    db = DBGroups(current_user.group)
    track = db.get_track(_id=track_id)
    agent = db.get_agent(current_user.id)
    if agent.manager > 1:
        db.delete_track(track_id)
    return redirect(url_for('list_tracks', company=track.company))


@app.route('/clients')
@login_required
def clients():
    db = DBGroups(current_user.group)
    clients_list = db.get_all_clients()
    return render_template('list_clients.xhtml', clients_list=clients_list, sum_clients=len(clients_list))


@app.route('/edit_client/<client_id>', methods=['GET', 'POST'])
@login_required
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
        send_mail(current_user.group, email, request.host_url + 'signup')
        return redirect(url_for('agents'))
    return render_template('new_agent.xhtml')


@app.route('/edit_agent/<agent_id>', methods=['GET', 'POST'])
@login_required
def edit_agent(agent_id):
    db = DBGroups(current_user.group)
    if db.get_agent(current_user.id).manager < 2:
        return 'Not Found', 404
    agent = db.get_agent(agent_id)
    if request.method == 'POST':
        db.update_agent(agent_id, {k: v for k, v in request.form.items()})
        return redirect(url_for('agents'))
    return render_template('edit_agent.xhtml', agent=agent)


@app.route('/forget_my_password', methods=['GET', 'POST'])
def forget_my_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = DBUsers().get_user(email)
        if not user:
            return render_template('forget_my_password.xhtml',
                                   msg='משתמש לא נמצא, נא נסה שוב.')
        send_mail(user.group, email, request.host_url + 'update_password', 'שיחזור סיסמה')
        return render_template('forget_my_password.xhtml',
                               msg='השיחזור הצליח! נשלח לך מייל עם קישור לבחירת סיסמה חדשה.')
    return render_template('forget_my_password.xhtml', msg='נא הכנס את כתובת האימייל שלך.')


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
        month = datetime.datetime.today().month
    if not year or not str(year).isdigit() or action == 'today':
        year = datetime.datetime.today().year
    date_filter = datetime.datetime(int(year), int(month), 1)

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
    send_basic_mail('yakir@ravtech.co.il', 'שלום טסט2', 'טסט טקסט')
    db = DBGroups(current_user.group)
    if db.get_agent(current_user.id).manager < 1:
        return 'Not Found', 404
    if request.method == 'POST':
        status = request.form.get('status')
        comment = request.form.get('comment')
        tran_id = int(request.form.get('tran_id'))

        db.update_transactions(tran_id, {'status': int(status),
                                         'comment': comment})
        tran_data = db.get_transaction(tran_id)
        send_basic_mail(to=tran_data.agent_id, subject='Connection Status',
                        contents='The connection you wrote to {} {}'.format(
                            tran_data.client_id,
                            'Success' if int(status) == 1 else 'Fail'))
    sales = db.get_status_sales()
    return render_template('status_sales.xhtml', sales=sales)


@app.route('/remove_sale/<_id>', methods=['GET'])
@login_required
def remove_sale(_id):
    db = DBGroups(current_user.group)
    if db.get_agent(current_user.id).manager > 1:
        remove_full_stack_transaction(current_user.id, _id)
    return redirect(url_for('status_sales'))


@app.route('/massages', methods=['GET', 'POST'])
@login_required
def massages():
    db = DBGroups(current_user.group)
    if db.get_agent(current_user.id).manager < 2:
        return redirect(url_for('index'))
    if request.method == 'POST':
        set_news([v for _, v in request.form.items()])
    return render_template('massages.xhtml', massage=[(k, v) for k, v in enumerate(get_news())])


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
