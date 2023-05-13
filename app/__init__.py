import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth

from app.utils import validation_class
from config import Config

db = SQLAlchemy()
login = LoginManager()
oauth = OAuth()
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page.'


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    login.init_app(app)
    db.init_app(app)
    oauth.init_app(app)

    with app.app_context():
        db.create_all()

    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    app.jinja_env.filters['validation_class'] = validation_class

    if app.debug:
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    return app


# Importing models
from app import models
