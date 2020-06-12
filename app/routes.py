import json
import datetime
import math

from flask import render_template, flash, redirect, url_for

from app import app, db
from app.forms import RadioForm
from app.models import PokerRange

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

    if form.validate_on_submit():
        if new_range == '':
            flash("Aucun combo n'a été sélectionné")
        else:
            query = PokerRange.query.filter_by(phero=phero, pvillain=pvillain, num_range=num_range).first()
            range_vierge = range_vierge.to_dict()
            poker_range = json.loads(range_vierge['poker_range'])
            for hand, actions in json.loads(new_range).items():
                poker_range[hand] = actions
            if query is None:
                rg = PokerRange(phero=phero, pvillain=pvillain, num_range=num_range, poker_range=json.dumps(poker_range))
                db.session.add(rg)
                db.session.commit()
                flash('La range {} vs {} N°{} a été ajoutée à la base de données'.format(phero, pvillain, num_range))
            else:
                query.poker_range = json.dumps(poker_range)
                db.session.commit()
                flash('La range {} vs {} N°{} a bien été mise à jour'.format(phero, pvillain, num_range))
        return render_template('modify_range.html', form=form)
    else:
        return render_template('modify_range.html', form=form)

@app.route('/ranges/<phero>/<pvillain>/<int:num_range>/')
def lire_ranges(phero, pvillain, num_range):
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
    liste_range = PokerRange.query.filter_by(phero=phero, pvillain=pvillain).all()
    test_range = PokerRange.query.filter_by(phero=phero, pvillain=pvillain, num_range=num_range).all()
    if (len(liste_range) == 0) or (num_range != 0 and len(test_range) == 0):
        poker_range = PokerRange.query.filter_by(phero='NA', pvillain='NA', num_range=0).first()
        flash('Aucune range définie pour cette situation')
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
            poker_range = PokerRange.query.filter_by(phero=phero, pvillain=pvillain, num_range=num_range).first()
            return render_template('read_range.html', title='Lecture', form=form, phero=phero, pvillain=pvillain, poker_range=json.loads(str(poker_range)))

