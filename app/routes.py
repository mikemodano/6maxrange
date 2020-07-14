import json
import datetime
import math

from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user
from werkzeug.urls import url_parse

from app import app, db, mail
from app.forms import RadioForm, RegistrationForm, LoginForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import PokerRange, User
from app.email import send_password_reset_email

@app.route('/')
@app.route('/index/')
def index():
    return redirect(url_for('lire_ranges', phero='BB', pvillain='BU', num_range=1))

@app.route('/modifier_ranges', methods=['GET', 'POST'])
def modifier_ranges():
    form = RadioForm()
    phero = form.phero.data
    pvillain = form.pvillain.data
    num_range = form.num_range.data
    new_range = form.new_range.data
    all_pvillain = [('UO', 'UO'), ('SB', 'vs SB'), ('BU', 'vs BU'), ('CO', 'vs CO'), ('MP', 'vs MP'), ('UTG', 'vs UTG')]
    form.pvillain.choices = all_pvillain
    range_vierge = PokerRange.query.filter_by(phero='NA', pvillain='NA', num_range=0).first()
    if current_user.is_anonymous:
        flash("Vous devez être connecté pour créer des ranges")
        return redirect(url_for('login'))
    if form.validate_on_submit() and current_user.is_authenticated:
        if current_user.id == 2:
            flash("Les ranges ne sont pas modifiables pour ce compte")
            return redirect(url_for('modifier_ranges'))
        else:
            if new_range == '':
                flash("Aucun combo n'a été sélectionné")
            else:
                query = PokerRange.query.filter_by(phero=phero, pvillain=pvillain, num_range=num_range, user_id=current_user.id).first()
                range_vierge = range_vierge.to_dict()
                poker_range = json.loads(range_vierge['poker_range'])
                for hand, actions in json.loads(new_range).items():
                    poker_range[hand] = actions
                if query is None:
                    rg = PokerRange(phero=phero, pvillain=pvillain, num_range=num_range, poker_range=json.dumps(poker_range), user_id=current_user.id)
                    db.session.add(rg)
                    db.session.commit()
                    flash('La range {} vs {} N°{} a été ajoutée à la base de données'.format(phero, pvillain, num_range))
                else:
                    query.poker_range = json.dumps(poker_range)
                    db.session.commit()
                    flash("La range {} vs {} N°{} a bien été mise à jour".format(phero, pvillain, num_range))
            return redirect(url_for('modifier_ranges'))
    else:
        return render_template('modify_range.html', form=form)

@app.route('/ranges/<phero>/<pvillain>/<int:num_range>/')
def lire_ranges(phero, pvillain, num_range):
    if current_user.is_anonymous:
        flash("Vous devez être connecté pour lire des ranges")
        return redirect(url_for('login'))
    else:
        form = RadioForm()
        all_pvillain = [('SB', 'vs SB'), ('BU', 'vs BU'), ('CO', 'vs CO'), ('MP', 'vs MP'), ('UTG', 'vs UTG'), ('UO', 'UO')]
        if phero == 'BB':
            all_pvillain.remove(('UO', 'UO'))
            list_pvillain = all_pvillain
        else:
            list_pvillain = all_pvillain[-(5-all_pvillain.index((phero, "vs " + phero))):]
        form.pvillain.choices = list_pvillain
        form.pvillain.data = pvillain
        form.phero.data = phero
        date = datetime.datetime.now()
        minutes = date.minute
        liste_range = PokerRange.query.filter_by(phero=phero, pvillain=pvillain, user_id=current_user.id).all()
        test_range = PokerRange.query.filter_by(phero=phero, pvillain=pvillain, num_range=num_range, user_id=current_user.id).all()
        if (len(liste_range) == 0) or (num_range != 0 and len(test_range) == 0):
            poker_range = PokerRange.query.filter_by(phero='NA', pvillain='NA', num_range=0).first()
            flash("Aucune range définie pour cette situation")
            return render_template('read_range.html', title='Lecture', form=form, pvillain=pvillain, phero=phero, poker_range=json.loads(str(poker_range)))
        else:
            nb_range = len(liste_range)
            if num_range == 0:
                if minutes == 0:
                    num_range = 1
                else:
                    num_range = math.ceil(minutes/(60/nb_range))
                return redirect(url_for('lire_ranges', phero=phero, pvillain=pvillain, num_range=num_range))
            else:
                form.num_range.data = num_range
                poker_range = PokerRange.query.filter_by(phero=phero, pvillain=pvillain, num_range=num_range, user_id=current_user.id).first()
                return render_template('read_range.html', title='Lecture', form=form, phero=phero, pvillain=pvillain, poker_range=json.loads(str(poker_range)))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Se connecter', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Bienvenue {}, ton compte a été créé!".format(form.username.data))
        return redirect(url_for('modifier_ranges'))
    return render_template('register.html', title='Register', form=form)

@app.route('/account', methods=['GET', 'POST'])
def mon_compte():
    return render_template('account.html', title='Mon compte')

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Veuillez vérifier vos email et suivez les instructions')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',title='Changer de mot de passe', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Votre mot de passe a été changé')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)