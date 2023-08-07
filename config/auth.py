from authlib.integrations.flask_client import OAuth
from flask_login import LoginManager

login = LoginManager()
oauth = OAuth()

def init_auth(app):
    # Login Manager setup
    login.login_view = 'auth.login'
    login.login_message = 'Please log in to access this page.'
    login.init_app(app)

    # OAuth setup
    oauth.init_app(app)
