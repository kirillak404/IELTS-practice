import os

from amplitude import Amplitude
from authlib.integrations.flask_client import OAuth
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from config import Config

db = SQLAlchemy()
login = LoginManager()
oauth = OAuth()
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page.'
amplitude = Amplitude(os.environ.get('AMPLITUDE_API_KEY'))


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    login.init_app(app)
    db.init_app(app)
    oauth.init_app(app)

    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_SDK_DSN'),
        integrations=[
            FlaskIntegration(),
        ],
        send_default_pii=True,

        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0
    )

    with app.app_context():
        # importing models
        from app import models

        # creating database
        db.create_all()

        # creating tables if not exists
        if not models.Section.query.first():
            from app.utils import create_and_fill_out_tables
            create_and_fill_out_tables(models)

    # register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.utils import convert_answer_object_to_html, time_ago_in_words, show_score_with_emoji
    app.jinja_env.filters['time_ago_in_words'] = time_ago_in_words
    app.jinja_env.filters['show_score_with_emoji'] = show_score_with_emoji
    app.jinja_env.globals['convert_answer_object_to_html'] = convert_answer_object_to_html
    return app
