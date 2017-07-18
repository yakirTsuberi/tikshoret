# -*- coding: utf-8 -*-

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
from .pkgs.utils import check_client, get_my_sales, send_mail, sum_connections, SIM_START_WITH, \
    get_news, set_news, remove_full_stack_transaction, send_basic_mail, get_contents, write_to_drive, remove_user, \
    update_all_tracks, set_all_tracks, get_status_sales, get_later_sales

login_manager = LoginManager()
app = Flask(__name__)
login_manager.init_app(app)


class User(UserMixin):
    pass


@login_manager.user_loader
def user_loader(_id):
    db = DBUsers()
    user_db = db.get_user(id=_id)
    if not user_db:
        return
    user = User()
    user.id = user_db.id
    user.email = user_db.email
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
    user_db = db.get_all_users(email)
    group = request.form.get('group')
    print(group)
    if len(user_db) > 1 and not group:
        print(user_db)
        return render_template('login.xhtml', massage='False', groups=user_db)
    if user_db:
        if user_db[0].pw == password:
            user = User()
            if group:
                group = eval(group)
                user.id = group[0]
                user.email = email
                user.group = group[3]
            else:
                user.id = user_db[0].id
                user.email = email
                user.group = user_db[0].group
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
    user = db.get_agent(current_user.email)
    return render_template('index.xhtml', user=user, news=get_news())


@app.route('/setting')
@login_required
def setting():
    return ''


@app.route('/my_sales', defaults={'agent_id': ''})
@app.route('/my_sales/<agent_id>')
@login_required
def my_sales(agent_id):
    db = DBGroups(current_user.group)
    print(current_user.group)
    if db.get_agent(current_user.email).manager > 1:
        agent_id = agent_id or current_user.email
    else:
        agent_id = current_user.email
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
    sales = get_my_sales(current_user.group, agent_id, date_filter)
    sum_price = sum([i[0].price for i in sales])
    return render_template('my_sales.xhtml', sales=sales,
                           month=month, year=year,
                           sum_sale=len(sales), sum_price=sum_price,
                           agent_id=agent_id)


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
    for contents in all_c:
        ba = db.get_bank_account(contents.client_id) or []
        cc = db.get_credit_card(contents.client_id) or []
        if cc:
            tmp = []
            for k, v in enumerate(cc):
                if k == 2:
                    tmp.append(v[-4:].rjust(len(v), "*"))
                else:
                    tmp.append(v)
            cc = tmp
        clients_list.append([contents, ba, cc])
    tracks = db.get_all_tracks(company)
    if request.method == 'POST':

        track = request.form.get('track')
        passport = request.form.get('passport')

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

        # Comment
        comment = request.form.get('comment')

        # Check Client
        errors = check_client(client_id if passport != 'on' else None, first_name, last_name, address, city, phone,
                              email)

        # Check CreditCard
        if all([credit_card, month, year, cvv]):
            if '*' in credit_card:
                credit_card = db.get_secure_credit_card(credit_card[-4:])
            checked_credit_card = True  # check_credit_card(credit_card, month, year, cvv)
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
                db_credit_card = db.get_credit_card(client_id)
                if not db_credit_card:
                    db.set_credit_card(client_id, credit_card, month, year, cvv)
                if db_credit_card:
                    if credit_card[-4:] != db_credit_card.card_number[-4:] and len(credit_card) > 4:
                        db.update_credit_card(db_credit_card.id,
                                              {'card_number': credit_card, 'month': month, 'year': year, 'cvv': cvv})
                credit_card_id = db.get_credit_card(client_id).id
            if account_num:
                if not db.get_bank_account(client_id):
                    db.set_bank_account(client_id, account_num, brunch, bank)
                account_num_id = db.get_bank_account(client_id).id
            db.set_transactions(
                current_user.email,
                db.get_track(company=company, name=track).id,
                client_id,
                credit_card_id,
                account_num_id,
                datetime.datetime.today(),
                request.form.get('sim_num' + str(i)),
                request.form.get('phone_num' + str(i)),
                0,
                comment)
        agent_connect = db.get_agent(current_user.email)
        contents = get_contents(agent_connect, request.form, company)
        subject = 'חיבור חדש ללקוח: {} {}'.format(first_name, last_name)
        for agent in db.get_all_agents(manager=2):
            send_basic_mail(to=agent.email, subject=subject, contents=contents)
        if agent_connect.manager < 2:
            send_basic_mail(to=current_user.email, subject=subject, contents=contents)
        if email:
            send_basic_mail(to=email, subject=subject, contents=contents)
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

    agent = db.get_agent(current_user.email)
    tracks = db.get_all_tracks(company=company)
    tags = db.get_all_tags()
    return render_template('list_tracks.xhtml', company=company, tracks=tracks, user=agent, tags=tags)


@app.route('/new_track/<company>', methods=['GET', 'POST'])
@login_required
def new_track(company):
    if request.method == 'POST':
        db = DBGroups(current_user.group)

        agent = db.get_agent(current_user.email)
        if agent.manager > 1:
            price = request.form.get('price')
            name = request.form.get('name')
            tag = request.form.get('tag')
            description = request.form.get('description')

            set_all_tracks(company, price, name, description)
            # db.set_track(company, price, name, description)
            track_id = db.get_track(company=company, name=name).id
            if tag:
                db.set_tag(tag, track_id)
        return redirect(url_for('list_tracks', company=company))
    return render_template('new_track.xhtml', company=company)


@app.route('/edit_track/<track_id>', methods=['GET', 'POST'])
@login_required
def edit_track(track_id):
    db = DBGroups(current_user.group)
    track = db.get_track(_id=track_id)
    tags = db.get_all_tags(track_id=track.id)
    if request.method == 'POST':
        agent = db.get_agent(current_user.email)
        if agent.manager < 2:
            return 'Permission Denied', 404
        tmp = {}
        for k, v in request.form.items():
            if str(k).startswith('tag'):
                tag_id = int(k.replace('tag', ''))
                if tag_id > 0:
                    db.update_tag(tag_id, {'name': v})
                else:
                    if v:
                        db.set_tag(v, track_id)
            else:
                tmp[k] = v
        update_all_tracks(track_id, {k: v for k, v in tmp.items()})
        # db.update_track(track_id, {k: v for k, v in tmp.items())

        return redirect(url_for('list_tracks', company=track.company))
    return render_template('edit_track.xhtml', track=track, tags=tags)


@app.route('/delete_track/<track_id>')
@login_required
def delete_track(track_id):
    db = DBGroups(current_user.group)
    track = db.get_track(_id=track_id)
    agent = db.get_agent(current_user.email)
    if agent.manager > 1:
        db.delete_track(track_id)
    return redirect(url_for('list_tracks', company=track.company))


@app.route('/delete_agent/<agent_id>')
@login_required
def delete_agent(agent_id):
    db = DBGroups(current_user.group)
    agent = db.get_agent(current_user.email)
    if agent.manager > 0:
        remove_user(agent_id)
    return redirect(url_for('agents'))


@app.route('/clients')
@login_required
def clients():
    db = DBGroups(current_user.group)
    agent = db.get_agent(current_user.email)
    search = request.args.get('search')
    if agent.manager < 1:
        clients_list = [client.Clients for client in db.get_all_clients(current_user.email, search)]
    else:
        clients_list = db.get_all_clients(search=search)
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
    agent = db.get_agent(current_user.email)
    if agent.manager == 0:
        return 'Not Found', 404
    agents_list = []
    if agent.manager == 1:
        agents_list = db.get_all_agents(manager=0)
    if agent.manager == 2:
        agents_list = db.get_all_agents()
    return render_template('list_agents.xhtml', agents_list=agents_list)


@app.route('/new_agent', methods=['GET', 'POST'])
@login_required
def new_agent():
    db = DBGroups(current_user.group)
    agent_manager = db.get_agent(current_user.email).manager
    if agent_manager < 1:
        return 'Not Found', 404
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        manager = request.form.get('manager')
        if manager is None:
            manager = 0
        phone = request.form.get('phone')
        db.set_agent(email=email, first_name=first_name, last_name=last_name, manager=manager, phone=phone or None)
        send_mail(current_user.group, email, request.host_url + 'signup')
        return redirect(url_for('agents'))
    return render_template('new_agent.xhtml', agent_manager=agent_manager)


@app.route('/edit_agent/<agent_id>', methods=['GET', 'POST'])
@login_required
def edit_agent(agent_id):
    db = DBGroups(current_user.group)
    agent_manager = db.get_agent(current_user.email).manager
    if agent_manager < 1:
        return 'Not Found', 404
    agent = db.get_agent(agent_id)
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        manager = request.form.get('manager')
        if manager is None:
            manager = 0
        db.update_agent(agent_id, dict(first_name=first_name, last_name=last_name, phone=phone, manager=manager))
        return redirect(url_for('agents'))
    return render_template('edit_agent.xhtml', agent=agent, agent_manager=agent_manager)


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
    if db.get_agent(current_user.email).manager < 1:
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
    db = DBGroups(current_user.group)
    if db.get_agent(current_user.email).manager < 2:
        return 'Not Found', 404
    if request.method == 'POST':
        status = request.form.get('status')
        comment = request.form.get('comment')
        tran_id = int(request.form.get('tran_id'))
        reminds = request.form.get('reminds')

        group = request.form.get('group')

        values = {'comment': comment}

        if reminds:
            reminds = datetime.datetime.strptime(reminds, '%d %B, %Y')
            print(reminds)
            values['reminds'] = reminds.date()

        if status:
            values['status'] = int(status)

        db = DBGroups(group)
        db.update_transactions(tran_id, values)

        tran_data = db.get_transaction(tran_id)

        client = db.get_client(tran_data.client_id)

        if status:
            contents = 'מצב חיבור לקו: {} -{}-,\n הערה: {}'.format(tran_data.phone_num,
                                                                   'הצליח' if int(status) == 1 else 'נכשל',
                                                                   comment)
            subject = 'חיבור חדש ללקוח: {} {}'.format(client.first_name, client.last_name)

            send_basic_mail(to=tran_data.agent_id, subject=subject,
                            contents=contents)
            if int(status) == 1:
                agent = db.get_agent(tran_data.agent_id)
                c = db.get_credit_card(client.client_id)
                cc = '      '
                if c:
                    cc = c.card_number
                else:
                    c = db.get_bank_account(client.client_id)
                    if c:
                        cc = c.account_num

                track = db.get_track(_id=tran_data.track)
                write_to_drive([[agent.first_name + ' ' + agent.last_name,
                                 client.first_name + ' ' + client.last_name,
                                 client.client_id,
                                 cc[-4:],
                                 track.company,
                                 '',
                                 str(datetime.datetime.now().date())
                                 ]])
    return render_template('status_sales.xhtml', get_status_sales=get_status_sales())


@app.route('/later_sales', methods=['GET', 'POST'])
@login_required
def later_sales():
    if request.method == 'POST':
        print(request.form)
        db = DBGroups(request.form.get('group'))
        db.update_transactions(request.form.get('id'), {'reminds': None, 'status': 0})
        return redirect(url_for('status_sales'))
    return render_template('later_sales.xhtml', data=get_later_sales())


@app.route('/remove_sale/<_id>', methods=['GET'])
@login_required
def remove_sale(_id):
    db = DBGroups(current_user.group)
    if db.get_agent(current_user.email).manager > 1:
        remove_full_stack_transaction(current_user.email, _id)
    return redirect(url_for('status_sales'))


@app.route('/massages', methods=['GET', 'POST'])
@login_required
def massages():
    db = DBGroups(current_user.group)
    if db.get_agent(current_user.email).manager < 2:
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
