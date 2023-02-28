# -*- encoding: utf-8 -*-
"""
Copyright (c) Minu Kim - minu.kim@kaist.ac.kr
Templates from AppSeed.us

Some of the contents are hidden for privacy issues.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_sitemap import Sitemap
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login = LoginManager(app)
login.login_view = 'login'

mail = Mail(app)
bootstrap = Bootstrap(app)
sitemap = Sitemap(app) 


# Import routing, models and Start the App
from app import routes, models
