# -*- encoding: utf-8 -*-
"""
Copyright (c) Minu Kim - minu.kim@kaist.ac.kr
Templates from AppSeed.us
"""

from datetime import date
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, TextAreaField, SubmitField, PasswordField, SelectField
from wtforms.validators import InputRequired, Email, DataRequired, EqualTo


class LoginForm(FlaskForm):
    username = StringField(u'Username', validators=[DataRequired()])
    password = PasswordField(u'Password', validators=[DataRequired()])


class RegisterForm(FlaskForm):
    current_year = date.today().year
    list_year = [(year, year) for year in range(current_year, 1987, -1)]
    name = StringField(u'Name')
    username = StringField(u'Username', validators=[DataRequired()])
    password = PasswordField(u'Password', validators=[DataRequired()])
    password2 = PasswordField(u'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    email = StringField(u'Email', validators=[DataRequired(), Email()])
    year = SelectField(u'Admitted Year', choices=list_year, validators=[DataRequired()])


class ResetPasswordForm(FlaskForm):
    password = PasswordField(u'Password', validators=[DataRequired()])
    password2 = PasswordField(u'Repeat Password', validators=[DataRequired(), EqualTo('password')])
