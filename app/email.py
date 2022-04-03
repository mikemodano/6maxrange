from threading import Thread

from flask_mail import Message
from flask import render_template

from app import mail, app


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('[6maxpokerrange] Changer son mot de passe',
               sender=app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt', user=user, token=token),
               html_body=render_template('email/reset_password.html', user=user, token=token))


def send_following_hh(following_hh, sujet='[6maxpokerrange] - Mains à revoir'):
    send_email(sujet,
               sender=app.config['ADMINS'][0],
               recipients=['aurelien.vigne@free.fr'],
               text_body=render_template('email/following_hh.txt', following_hh=following_hh),
               html_body=render_template('email/following_hh.html', following_hh=following_hh))


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()