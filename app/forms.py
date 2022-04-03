from flask_wtf import FlaskForm
from wtforms import RadioField, HiddenField, SubmitField, StringField, PasswordField, BooleanField, MultipleFileField, \
    IntegerField
from wtforms.fields.html5 import DateField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, NumberRange, Optional
from app.models import User


class RadioForm(FlaskForm):
    phero = RadioField('phero', choices=[('BB', 'BB'), ('SB', 'SB'), ('BU', 'BU'), ('CO', 'CO'), ('MP', 'MP'),
                                         ('UTG', 'UTG')])
    pvillain = RadioField('pvillain', choices=[])
    num_range = RadioField('num_range', choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4')])
    new_range = HiddenField("new_range")
    addrange = SubmitField('<img class="img-fluid rounded" src="/static/images/plus_button.png"/>')
    removerange = SubmitField('<img class="img-fluid rounded" src="/static/images/moins_button.png"/>')
    submit = SubmitField("submit")


class LoginForm(FlaskForm):
    username = StringField("Nom d'utilisateur", validators=[DataRequired("Veuillez renseigner ce champ")])
    password = PasswordField('Mot de passe', validators=[DataRequired("Veuillez renseigner ce champ")])
    remember_me = BooleanField('Se souvenir de moi')
    submit = SubmitField("Se connecter")


class RegistrationForm(FlaskForm):
    username = StringField("Nom d'utilisateur", validators=[DataRequired("Veuillez renseigner ce champ")])
    email = StringField('Email', validators=[DataRequired("Le champ est vide"),
                                             Email("L'adresse utilisée n'est pas valide")])
    password = PasswordField('Mot de passe', validators=[DataRequired("Veuillez renseigner ce champ")])
    password2 = PasswordField('Mot de passe', validators=[DataRequired("Veuillez renseigner ce champ"),
                                                          EqualTo('password',
                                                                  message="Les 2 mots de passe ne correspondent pas")])
    submit = SubmitField("S'enregistrer")

    @staticmethod
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError("Merci d'utiliser un autre nom d'utilisateur")

    @staticmethod
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError("Merci d'utiliser une autre adresse email")


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired("Veuillez renseigner ce champ"),
                                             Email("L'adresse utilisée n'est pas valide")])
    submit = SubmitField('Changer son mot de passe')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Mot de passe', validators=[DataRequired("Veuillez renseigner ce champ")])
    password2 = PasswordField('Mot de passe', validators=[DataRequired("Veuillez renseigner ce champ"),
                                                          EqualTo('password',
                                                                  message="Les 2 mots de passe ne correspondent pas")])
    submit = SubmitField('Changer son mot de passe')


class UploadForm(FlaskForm):
    uploads = MultipleFileField('uploads', validators=[DataRequired("Veuillez renseigner ce champ")])
    submit = SubmitField('Importer')


class LeakFinderForm(FlaskForm):
    rooms = RadioField(choices=[], default='0', validators=[Optional()])
    limits = RadioField(choices=[], default='0', validators=[Optional()])
    lasthands = IntegerField(validators=[NumberRange(min=10000, max=None, message='Minimum 10 000 mains'), Optional()])
    date_debut = DateField('Filtrer du', validators=[Optional()], format='%Y-%m-%d')
    date_fin = DateField('au', validators=[Optional()], format='%Y-%m-%d')
    filtre = SubmitField('Vérifier le nombre de mains')
    submit = SubmitField('Créer un rapport')
