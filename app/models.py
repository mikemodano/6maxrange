import datetime

from sqlalchemy_serializer import SerializerMixin
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app import login

class PokerRange(db.Model, SerializerMixin):
    __tablename__ = 'pokerrange'
    id = db.Column(db.Integer, primary_key=True)
    phero = db.Column(db.String(10))
    pvillain = db.Column(db.String(10))
    num_range = db.Column(db.Integer)
    poker_range = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

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

    def __repr__(self):
        return '<User {}>'.format(self.username)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))