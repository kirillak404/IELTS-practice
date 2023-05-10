import os

from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy

from app.utils import validation_class


# creating Flask app object
app = Flask(__name__)

# define folder for saving audio files
UPLOAD_FOLDER = "uploaded_audio"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# set up sessions
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
app.config["SESSION_PERMANENT"] = False
Session(app)

# Creating SQLAlchemy object for working with database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db = SQLAlchemy(app)

# define validation form class
app.jinja_env.filters['validation_class'] = validation_class


# Importing routes
from app import routes

# Importing models
from app import models

