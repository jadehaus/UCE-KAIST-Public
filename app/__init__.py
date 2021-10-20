# -*- encoding: utf-8 -*-
"""
Copyright (c) Minu Kim - minu.kim@kaist.ac.kr
Templates from AppSeed.us
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from config import Config


# Grabs the folder where the script runs.
# basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)  # flask-sqlalchemy
migrate = Migrate(app, db)

login = LoginManager(app)  # flask-loginmanager
login.login_view = 'login'  # init the login manager

mail = Mail(app)
bootstrap = Bootstrap(app)


# Import routing, models and Start the App
from app import routes, models