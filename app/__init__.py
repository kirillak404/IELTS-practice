from flask import Flask

from config import Config, init_db, init_auth, init_jinja_filters, init_sentry


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Apply configurations
    init_db(app)
    init_auth(app)
    init_jinja_filters(app)
    init_sentry(app)

    # register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    return app
