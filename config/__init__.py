import os

class Config(object):
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('POSTGRES_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # Limit file size to 1 MB

from .database import init_db
from .auth import init_auth
from .jinja_filters import init_jinja_filters
from .sentry import init_sentry