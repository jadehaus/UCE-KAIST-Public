from threading import Thread
from flask import render_template
from flask_mail import Message
from app import app, mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('[매화수] 비밀번호 재설정',
               sender='graduate.kaist.noreply@gmail.com',
               recipients=[user.email],
               text_body=render_template('email/reset_password_request.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password_request.html',
                                         user=user, token=token)
               )
