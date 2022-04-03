import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ca-cest-ma-cle--secretee'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # email server
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = '6maxpokerrange@gmail.com'
    MAIL_PASSWORD = 'qliuiiualsxpdell'
    ADMINS = ['6maxpokerrange@gmail.com', 'aurelien.vigne@free.fr']

    UPLOAD_PATH = os.path.join(basedir, 'app', 'static', 'uploads')
    UPLOAD_EXTENSIONS = ['.txt']

    BOOTSTRAP_BTN_STYLE = 'primary'  # default to 'secondary'


