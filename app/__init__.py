from authlib.integrations.flask_client import OAuth
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

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

    from app.utils import convert_answer_object_to_html, time_ago_in_words, get_speaking_overall_score_and_emoji
    app.jinja_env.filters['time_ago_in_words'] = time_ago_in_words
    app.jinja_env.globals['convert_answer_object_to_html'] = convert_answer_object_to_html
    app.jinja_env.globals['get_speaking_overall_score_and_emoji'] = get_speaking_overall_score_and_emoji
    return app
