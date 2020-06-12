from flask_wtf import FlaskForm
from wtforms import RadioField, HiddenField, SubmitField

class RadioForm(FlaskForm):
    phero = RadioField('hero_pos', choices=[('BB', 'BB'), ('SB', 'SB'), ('BU', 'BU'), ('CO', 'CO'), ('MP', 'MP'), ('UTG', 'UTG')])
    pvillain = RadioField('hero_pos', choices=[])
    num_range = RadioField('num_range', choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4')])
    new_range = HiddenField("new_range")
    submit = SubmitField("Submit")
