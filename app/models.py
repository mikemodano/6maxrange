import datetime
import jwt
from time import time
import json

from sqlalchemy_serializer import SerializerMixin
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import JSON

from app import db, login, app


class PokerRange(db.Model, SerializerMixin):
    __tablename__ = 'pokerrange'
    id = db.Column(db.Integer, primary_key=True)
    phero = db.Column(db.String(10))
    pvillain = db.Column(db.String(10))
    num_range = db.Column(db.Integer)
    poker_range = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self):
        emptyrange = {"_AA": "btn btn-info px-0", "_AKs": "btn btn-info px-0", "_AQs": "btn btn-info px-0",
                      "_AJs": "btn btn-info px-0", "_ATs": "btn btn-info px-0", "_A9s": "btn btn-info px-0",
                      "_A8s": "btn btn-info px-0", "_A7s": "btn btn-info px-0", "_A6s": "btn btn-info px-0",
                      "_A5s": "btn btn-info px-0", "_A4s": "btn btn-info px-0", "_A3s": "btn btn-info px-0",
                      "_A2s": "btn btn-info px-0", "_AKo": "btn btn-info px-0", "_KK": "btn btn-info px-0",
                      "_KQs": "btn btn-info px-0", "_KJs": "btn btn-info px-0", "_KTs": "btn btn-info px-0",
                      "_K9s": "btn btn-info px-0", "_K8s": "btn btn-info px-0", "_K7s": "btn btn-info px-0",
                      "_K6s": "btn btn-info px-0", "_K5s": "btn btn-info px-0", "_K4s": "btn btn-info px-0",
                      "_K3s": "btn btn-info px-0", "_K2s": "btn btn-info px-0", "_AQo": "btn btn-info px-0",
                      "_KQ": "btn btn-info px-0", "_QQ": "btn btn-info px-0", "_QJs": "btn btn-info px-0",
                      "_QTs": "btn btn-info px-0", "_Q9s": "btn btn-info px-0", "_Q8s": "btn btn-info px-0",
                      "_Q7s": "btn btn-info px-0", "_Q6s": "btn btn-info px-0", "_Q5s": "btn btn-info px-0",
                      "_Q4s": "btn btn-info px-0", "_Q3s": "btn btn-info px-0", "_Q2s": "btn btn-info px-0",
                      "_AJo": "btn btn-info px-0", "_KJo": "btn btn-info px-0", "_QJo": "btn btn-info px-0",
                      "_JJ": "btn btn-info px-0", "_JTs": "btn btn-info px-0", "_J9s": "btn btn-info px-0",
                      "_J8s": "btn btn-info px-0", "_J7s": "btn btn-info px-0", "_J6s": "btn btn-info px-0",
                      "_J5s": "btn btn-info px-0", "_J4s": "btn btn-info px-0", "_J3s": "btn btn-info px-0",
                      "_J2s": "btn btn-info px-0", "_ATo": "btn btn-info px-0", "_KTo": "btn btn-info px-0",
                      "_QTo": "btn btn-info px-0", "_JTo": "btn btn-info px-0", "_TT": "btn btn-info px-0",
                      "_T9s": "btn btn-info px-0", "_T8s": "btn btn-info px-0", "_T7s": "btn btn-info px-0",
                      "_T6s": "btn btn-info px-0", "_T5s": "btn btn-info px-0", "_T4s": "btn btn-info px-0",
                      "_T3s": "btn btn-info px-0", "_T2s": "btn btn-info px-0", "_A9o": "btn btn-info px-0",
                      "_K9o": "btn btn-info px-0", "_Q9o": "btn btn-info px-0", "_J9o": "btn btn-info px-0",
                      "_T9o": "btn btn-info px-0", "_99": "btn btn-info px-0", "_98s": "btn btn-info px-0",
                      "_97s": "btn btn-info px-0", "_96s": "btn btn-info px-0", "_95s": "btn btn-info px-0",
                      "_94s": "btn btn-info px-0", "_93s": "btn btn-info px-0", "_92s": "btn btn-info px-0",
                      "_A8o": "btn btn-info px-0", "_K8o": "btn btn-info px-0", "_Q8o": "btn btn-info px-0",
                      "_J8o": "btn btn-info px-0", "_T8o": "btn btn-info px-0", "_98o": "btn btn-info px-0",
                      "_88": "btn btn-info px-0", "_87s": "btn btn-info px-0", "_86s": "btn btn-info px-0",
                      "_85s": "btn btn-info px-0", "_84s": "btn btn-info px-0", "_83s": "btn btn-info px-0",
                      "_82s": "btn btn-info px-0", "_A7o": "btn btn-info px-0", "_K7o": "btn btn-info px-0",
                      "_Q7o": "btn btn-info px-0", "_J7o": "btn btn-info px-0", "_T7o": "btn btn-info px-0",
                      "_97o": "btn btn-info px-0", "_87o": "btn btn-info px-0", "_77": "btn btn-info px-0",
                      "_76s": "btn btn-info px-0", "_75s": "btn btn-info px-0", "_74s": "btn btn-info px-0",
                      "_73s": "btn btn-info px-0", "_72s": "btn btn-info px-0", "_A6o": "btn btn-info px-0",
                      "_K6o": "btn btn-info px-0", "_Q6o": "btn btn-info px-0", "_J6o": "btn btn-info px-0",
                      "_T6o": "btn btn-info px-0", "_96o": "btn btn-info px-0", "_86o": "btn btn-info px-0",
                      "_76o": "btn btn-info px-0", "_66": "btn btn-info px-0", "_65s": "btn btn-info px-0",
                      "_64s": "btn btn-info px-0", "_63s": "btn btn-info px-0", "_62s": "btn btn-info px-0",
                      "_A5o": "btn btn-info px-0", "_K5o": "btn btn-info px-0", "_Q5o": "btn btn-info px-0",
                      "_J5o": "btn btn-info px-0", "_T5o": "btn btn-info px-0", "_95o": "btn btn-info px-0",
                      "_85o": "btn btn-info px-0", "_75o": "btn btn-info px-0", "_65o": "btn btn-info px-0",
                      "_55": "btn btn-info px-0", "_54s": "btn btn-info px-0", "_53s": "btn btn-info px-0",
                      "_52s": "btn btn-info px-0", "_A4o": "btn btn-info px-0", "_K4o": "btn btn-info px-0",
                      "_Q4o": "btn btn-info px-0", "_J4o": "btn btn-info px-0", "_T4o": "btn btn-info px-0",
                      "_94o": "btn btn-info px-0", "_84o": "btn btn-info px-0", "_74o": "btn btn-info px-0",
                      "_64o": "btn btn-info px-0", "_54o": "btn btn-info px-0", "_44": "btn btn-info px-0",
                      "_43s": "btn btn-info px-0", "_42s": "btn btn-info px-0", "_A3o": "btn btn-info px-0",
                      "_K3o": "btn btn-info px-0", "_Q3o": "btn btn-info px-0", "_J3o": "btn btn-info px-0",
                      "_T3o": "btn btn-info px-0", "_93o": "btn btn-info px-0", "_83o": "btn btn-info px-0",
                      "_73o": "btn btn-info px-0", "_63o": "btn btn-info px-0", "_53o": "btn btn-info px-0",
                      "_43o": "btn btn-info px-0", "_33": "btn btn-info px-0", "_32s": "btn btn-info px-0",
                      "_A2o": "btn btn-info px-0", "_K2o": "btn btn-info px-0", "_Q2o": "btn btn-info px-0",
                      "_J2o": "btn btn-info px-0", "_T2o": "btn btn-info px-0", "_92o": "btn btn-info px-0",
                      "_82o": "btn btn-info px-0", "_72o": "btn btn-info px-0", "_62o": "btn btn-info px-0",
                      "_52o": "btn btn-info px-0", "_42o": "btn btn-info px-0", "_32o": "btn btn-info px-0",
                      "_22": "btn btn-info px-0"}

        if PokerRange.query.filter_by(phero='NA', pvillain='NA', num_range=0).first() is None:
            rg = PokerRange(phero='NA', pvillain='NA', num_range=0, poker_range=json.dumps(emptyrange), user_id=None)
            db.session.add(rg)
            db.session.commit()
            app.logger.info('La range vide a été ajoutée à la base de données')

    def __repr__(self):
        return self.poker_range


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode({'reset_password': self.id, 'exp': time() + expires_in},app.config['SECRET_KEY'],
                          algorithm='HS256').decode('utf-8')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


class PokerHH(db.Model, SerializerMixin):
    __tablename__ = 'pokerhh'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    room = db.Column(db.String(10))
    hand_id = db.Column(db.String(10), index=True, unique=True)
    timestamp = db.Column(db.DateTime)
    level = db.Column(db.String(10))
    cards = db.Column(db.String(10))
    bbs = db.Column(db.Float)
    combo = db.Column(db.String(10))
    hand_type = db.Column(db.String(10))
    hero_PFAction = db.Column(db.String(10))
    hero_PFAction_simpl = db.Column(db.String(10))
    nb_joueur = db.Column(db.Integer)
    position = db.Column(db.String(10))
    firstraiser = db.Column(db.String(10))
    winner = db.Column(db.String(10))
    facing_preflop = db.Column(db.String(10))
    sawflop = db.Column(db.Boolean)
    flop = db.Column(db.String(10))
    type_flop = db.Column(db.String(10))
    flop_simpl = db.Column(db.String(10))
    nb_joueur_flop = db.Column(db.Integer)
    hero_line_F = db.Column(db.String(10))
    turn = db.Column(db.String(10))
    hero_line_T = db.Column(db.String(10))
    river = db.Column(db.String(10))
    hero_line_R = db.Column(db.String(10))
    hero_line = db.Column(db.String(10))
    sawshowdown = db.Column(db.Boolean)

    def __repr__(self):
        return self.level


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
