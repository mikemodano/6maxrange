import json
import datetime
import math
import os
import pandas as pd

from flask import render_template, flash, redirect, url_for, request, session, jsonify
from flask_login import current_user, login_user, logout_user
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from sqlalchemy import asc, desc
from jinja2 import Template

from app import app, db
from app.forms import RadioForm, RegistrationForm, LoginForm, ResetPasswordRequestForm, ResetPasswordForm, UploadForm, \
    LeakFinderForm
from app.models import PokerRange, User, PokerHH
from app.email import send_password_reset_email
from app.handhistoryconverter import HandHistoryConverter
from app.leakfinder import LeakFinder


@app.route('/')
@app.route('/index/')
def index():
    return redirect(url_for('lire_ranges', title='Lecture', phero='BB', pvillain='BU', num_range=1))


@app.route('/modifier_ranges/<phero>/<pvillain>/', methods=['GET', 'POST'])
def modifier_ranges(phero, pvillain):
    if current_user.is_anonymous:
        flash("Vous devez être connecté pour modifier des ranges")
        return redirect(url_for('login'))
    else:
        form = RadioForm()
        form.pvillain.data = pvillain
        form.phero.data = phero
        all_pvillain = [('SB', 'vs SB'), ('BU', 'vs BU'), ('CO', 'vs CO'), ('MP', 'vs MP'), ('UTG', 'vs UTG'),
                        ('UO', 'UO')]
        positions = ['UO', 'UTG', 'MP', 'CO', 'BU', 'SB', 'BB']
        if phero == 'BB':
            all_pvillain.remove(('UO', 'UO'))
            list_pvillain = all_pvillain
        else:
            list_pvillain = all_pvillain[-(5 - all_pvillain.index((phero, "vs " + phero))):]
        form.pvillain.choices = list_pvillain
        nbranges = PokerRange.query.filter_by(phero=phero, pvillain=pvillain, user_id=current_user.id).count()
        if positions.index(phero) < positions.index(pvillain):
            return redirect(url_for('modifier_ranges', phero=phero, pvillain='UO'))
        else:
            if request.method == 'POST' and current_user.is_authenticated and form.validate():
                if form.addrange.data:
                    newaddrange = PokerRange.query.filter_by(phero=phero, pvillain=pvillain, num_range=nbranges,
                                                             user_id=current_user.id).all()
                    rg = PokerRange(phero=phero, pvillain=pvillain, num_range=(nbranges+1),
                                    poker_range=json.dumps(json.loads(str(newaddrange[0]))), user_id=current_user.id)
                    db.session.add(rg)
                    db.session.commit()
                    flash('La range {} vs {} a été ajoutée à la base de données'.format(phero, pvillain))
                    return redirect(url_for('modifier_ranges', phero=phero, pvillain=pvillain))
                elif form.removerange.data:
                    rg = PokerRange.query.filter_by(phero=phero, pvillain=pvillain, num_range=nbranges,
                                                    user_id=current_user.id).first()
                    db.session.delete(rg)
                    db.session.commit()
                    flash('La ranges {} vs {} a été supprimée de la base de données'.format(phero, pvillain))
                    return redirect(url_for('modifier_ranges', phero=phero, pvillain=pvillain))
                elif form.submit.data:
                    new_ranges = json.loads(form.new_range.data.replace(' hand-edit', ''))

                    for idx, new_range in enumerate(new_ranges):
                        req = PokerRange.query.filter_by(phero=phero, pvillain=pvillain, num_range=(idx + 1),
                                                         user_id=current_user.id).first()
                        if req:
                            req.poker_range = json.dumps(new_range)
                        else:
                            rg = PokerRange(phero=phero, pvillain=pvillain, num_range=(idx + 1),
                                            poker_range=json.dumps(new_range), user_id=current_user.id)
                            db.session.add(rg)
                    db.session.commit()
                    flash('Les ranges {} vs {} ont été mises à jour dans la base de données'.format(phero, pvillain))

                    return redirect(url_for('modifier_ranges', phero=phero, pvillain=pvillain))
            else:
                req = PokerRange.query.filter_by(phero=phero, pvillain=pvillain, user_id=current_user.id)
                if req.count() == 0:
                    spot_ranges = PokerRange.query.filter_by(phero='NA', pvillain='NA', num_range=0).all()
                else:
                    spot_ranges = req.all()
                form.new_range.data = spot_ranges

                return render_template('modify_range.html', title='Modification', form=form, phero=phero, pvillain=pvillain,
                                       spot_ranges=json.loads(str(spot_ranges)), nbranges=nbranges)


@app.route('/ranges/<phero>/<pvillain>/<int:num_range>/')
def lire_ranges(phero, pvillain, num_range):
    if current_user.is_anonymous:
        flash("Vous devez être connecté pour lire des ranges")
        return redirect(url_for('login'))
    else:
        form = RadioForm()
        positions = ['UO', 'UTG', 'MP', 'CO', 'BU', 'SB', 'BB']
        all_pvillain = [('SB', 'vs SB'), ('BU', 'vs BU'), ('CO', 'vs CO'), ('MP', 'vs MP'), ('UTG', 'vs UTG'),
                        ('UO', 'UO')]
        if phero == 'BB':
            all_pvillain.remove(('UO', 'UO'))
            list_pvillain = all_pvillain
        else:
            list_pvillain = all_pvillain[-(5 - all_pvillain.index((phero, "vs " + phero))):]
        if positions.index(phero) < positions.index(pvillain):
            return redirect(url_for('lire_ranges', title='Lecture', phero=phero, pvillain='UO', num_range=num_range))
        else:
            form.pvillain.choices = list_pvillain
            form.pvillain.data = pvillain
            form.phero.data = phero
            date = datetime.datetime.now()
            minutes = date.minute
            liste_range = PokerRange.query.filter_by(phero=phero, pvillain=pvillain, user_id=current_user.id).all()
            test_range = PokerRange.query.filter_by(phero=phero, pvillain=pvillain, num_range=num_range,
                                                    user_id=current_user.id).all()
            if (len(liste_range) == 0) or (num_range != 0 and len(test_range) == 0):
                poker_range = PokerRange.query.filter_by(phero='NA', pvillain='NA', num_range=0).first()
                flash("Aucune range définie pour cette situation")
                return render_template('read_range.html', title='Lecture', form=form, pvillain=pvillain, phero=phero,
                                       poker_range=json.loads(str(poker_range)))
            else:
                nb_range = len(liste_range)
                if num_range == 0:
                    if minutes == 0:
                        num_range = 1
                    else:
                        num_range = math.ceil(minutes / (60 / nb_range))
                    return redirect(url_for('lire_ranges', title='Lecture', phero=phero, pvillain=pvillain,
                                            num_range=num_range))
                else:
                    form.num_range.data = num_range
                    poker_range = PokerRange.query.filter_by(phero=phero, pvillain=pvillain, num_range=num_range,
                                                             user_id=current_user.id).first()
                    return render_template('read_range.html', title='Lecture', form=form, phero=phero, pvillain=pvillain,
                                           poker_range=json.loads(str(poker_range)))


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
    if request.method == 'POST' and form.validate():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Bienvenue {}, ton compte a été créé!".format(form.username.data))
        return redirect(url_for('login'))
    return render_template('register.html', title="S'enregistrer", form=form)


@app.route('/account', methods=['GET', 'POST'])
def mon_compte():
    form = UploadForm()
    files_list = []
    if form.validate_on_submit():
        for uploaded_file in form.uploads.data:
            filename = secure_filename(uploaded_file.filename)
            if filename != '':
                file_ext = os.path.splitext(filename)[1]
                if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                    flash("Le format de ce fichier n'est pas pris en charge : %s" % file_ext)
                    return redirect(url_for('mon_compte'))
                repertoire = os.path.join(app.config['UPLOAD_PATH'], current_user.username)
                if not os.path.exists(repertoire):
                    os.mkdir(repertoire)
                uploaded_file.save(os.path.join(repertoire, filename))
                files_list.append(os.path.join(repertoire, filename))
        hhconverter = HandHistoryConverter(current_user.id, files_list)
        for file in files_list:
            os.remove(file)

        for msg in hhconverter.message:
            flash(msg)
    return render_template('account.html', title='Mon compte', form=form)


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
        else:
            flash('Cette adresse ne correspond à aucun compte')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', title='Changer de mot de passe', form=form)


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


@app.route('/leakfinder', methods=['GET', 'POST'])
def leakfinder():
    if current_user.is_anonymous:
        flash("Vous devez être connecté pour rechercher des leak")
        return redirect(url_for('login'))
    form = LeakFinderForm()
    liste_rooms = ['Toutes'] + [r.room for r in db.session.query(PokerHH.room).distinct().all()]
    liste_rooms = list(zip(sorted(liste_rooms, reverse=True), sorted(liste_rooms, reverse=True)))
    form.rooms.choices = liste_rooms
    liste_limites = ['Toutes'] + [r.level for r in db.session.query(PokerHH.level).distinct().all()]
    liste_limites = list(zip(sorted(liste_limites, reverse=True), sorted(liste_limites, reverse=True)))
    form.limits.choices = liste_limites
    nb_mains = PokerHH.query.filter_by(user_id=current_user.id).count()
    if request.method == 'POST' and form.validate():
        if form.filtre.data:
            selected_hands = PokerHH.query.filter_by(user_id=current_user.id)
            if form.rooms.data not in ['Toutes', 0]:
                selected_hands = selected_hands.filter_by(room=form.rooms.data)
            if form.limits.data not in ['Toutes', 0]:
                selected_hands = selected_hands.filter_by(level=form.limits.data)
            if form.date_debut.data:
                selected_hands = selected_hands.filter(PokerHH.timestamp >= form.date_debut.data)
            if form.date_fin.data:
                selected_hands = selected_hands.filter(PokerHH.timestamp <= form.date_fin.data)
            if form.lasthands.data:
                selected_hands = selected_hands.order_by(asc(PokerHH.timestamp)).limit(form.lasthands.data)
            nb_mains_filtres = selected_hands.count()
            flash("{} mains ont été sélectionnées".format(nb_mains_filtres))
            return render_template('leakfinder.html', title='Rechercher des leak', form=form, nb_mains=nb_mains,
                                   nb_mains_filtres=nb_mains_filtres)
        if form.submit.data:
            selected_hands = PokerHH.query.filter_by(user_id=current_user.id)
            if form.limits.data not in ['Toutes', 0]:
                selected_hands = selected_hands.filter_by(level=form.limits.data)
            if form.date_debut.data:
                selected_hands = selected_hands.filter(PokerHH.timestamp >= form.date_debut.data)
            if form.date_fin.data:
                selected_hands = selected_hands.filter(PokerHH.timestamp <= form.date_fin.data)
            if form.lasthands.data:
                selected_hands = selected_hands.order_by(desc(PokerHH.timestamp)).limit(form.lasthands.data)
            nb_mains_filtres = selected_hands.count()
            if nb_mains_filtres < 10000:
                flash("Vous devez sélectionner au moins 10 000 mains pour créer un rapport ({} mains sélectionées)"
                      .format(nb_mains_filtres))
                return render_template('leakfinder.html', title='Rechercher des leak', form=form, nb_mains=nb_mains,
                                       nb_mains_filtres=nb_mains_filtres)
            df = pd.read_sql(selected_hands.statement, selected_hands.session.bind)
            new_report = LeakFinder(df)
            session['nbHH'] = new_report.nbHH
            session['rtime'] = new_report.rtime
            session['startdate'] = new_report.startdate
            session['enddate'] = new_report.enddate
            session[' winrate'] = new_report.bbs_100
            session[' std_dev'] = new_report.std_dev_100
            session['tables'] = new_report.tables
            session['titres'] = new_report.titres
            session['noleak'] = new_report.noleak
            return redirect(url_for('report'))
    return render_template('leakfinder.html', title='Rechercher des leak', form=form, nb_mains=nb_mains)


@app.route('/report', methods=['GET', 'POST'])
def report():
    if current_user.is_anonymous:
        flash("Vous devez être connecté pour générer un rapport")
        return redirect(url_for('login'))
    nbHH = session['nbHH']
    rtime = session['rtime']
    startdate = session['startdate']
    enddate = session['enddate']
    winrate = session[' winrate']
    std_dev = session[' std_dev']
    tables = session['tables']
    noleak = session['noleak']
    flash("Rapport fait sur {} mains en {:1.0f} secondes".format(nbHH, rtime))
    return render_template('report.html', title='Rapport', nbHH=nbHH, startdate=startdate, enddate=enddate,
                           winrate=winrate, std_dev=std_dev, tables=tables, noleak=noleak)


@app.route('/page_test')
def page_test():

    return render_template('page_test.html')