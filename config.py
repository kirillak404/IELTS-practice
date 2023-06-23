import os


class Config(object):
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('POSTGRES_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False