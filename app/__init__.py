import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_dance.contrib.google import make_google_blueprint

from app.utils import validation_class

# creating Flask app object
app = Flask(__name__)

# define folder for saving audio files
UPLOAD_FOLDER = "uploaded_audio"

# App config
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # DELETE ON PRODUCTION
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["GOOGLE_OAUTH_CLIENT_ID"] = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
db = SQLAlchemy(app)

# setting up login
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# setting up Google OAuth
google_bp = make_google_blueprint(
    client_id=app.config["GOOGLE_OAUTH_CLIENT_ID"],
    client_secret=app.config["GOOGLE_OAUTH_CLIENT_SECRET"],
    scope=["openid", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"],
    offline=True,
    reprompt_consent=True,
)
app.register_blueprint(google_bp, url_prefix="/login")

# define validation form class
app.jinja_env.filters['validation_class'] = validation_class


# Importing routes
from app import routes

# Importing models
from app import models
