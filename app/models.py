import datetime

from sqlalchemy_serializer import SerializerMixin



from app import db

class PokerRange(db.Model, SerializerMixin):
    __tablename__ = 'pokerrange'
    id = db.Column(db.Integer, primary_key=True)
    phero = db.Column(db.String(10))
    pvillain = db.Column(db.String(10))
    num_range = db.Column(db.Integer)
    poker_range = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.now())

    def __repr__(self):
        return self.poker_range