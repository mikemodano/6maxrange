from flask_wtf import FlaskForm
from wtforms import RadioField, HiddenField, SubmitField, StringField, PasswordField, BooleanField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User

class RadioForm(FlaskForm):
    phero = RadioField('hero_pos', choices=[('BB', 'BB'), ('SB', 'SB'), ('BU', 'BU'), ('CO', 'CO'), ('MP', 'MP'), ('UTG', 'UTG')])
    pvillain = RadioField('hero_pos', choices=[])
    num_range = RadioField('num_range', choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4')])
    new_range = HiddenField("new_range")
    submit = SubmitField("Submit")

class LoginForm(FlaskForm):
    username = StringField("Nom d'utilisateur", validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    remember_me = BooleanField('Se souvenir de moi')
    submit = SubmitField("Se connecter")

class RegistrationForm(FlaskForm):
    username = StringField("Nom d'utilisateur", validators=[DataRequired("Le champ est vide")])
    email = StringField('Email', validators=[DataRequired("Le champ est vide"), Email("L'adresse utilisée n'est pas valide")])
    password = PasswordField('Mot de passe', validators=[DataRequired("Le champ est vide")])
    password2 = PasswordField('Mot de passe', validators=[DataRequired("Le champ est vide"), EqualTo('password', message="Les 2 mots de passe ne correspondent pas")])
    submit = SubmitField("S'enregistrer")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError("Merci d'utiliser un autre nom d'utilisateur")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError("Merci d'utiliser une autre adresse email")

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Changer son mot de passe')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    password2 = PasswordField('Mot de passe', validators=[DataRequired(), EqualTo('password', message="Les 2 mots de passe ne correspondent pas")])
    submit = SubmitField('Changer son mot de passe')