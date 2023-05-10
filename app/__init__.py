import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

from app.utils import validation_class

# creating Flask app object
app = Flask(__name__)

# define folder for saving audio files
UPLOAD_FOLDER = "uploaded_audio"

# App config
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
db = SQLAlchemy(app)

# set up login
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# define validation form class
app.jinja_env.filters['validation_class'] = validation_class


# Importing routes
from app import routes

# Importing models
from app import models
