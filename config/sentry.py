import os
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

def init_sentry(app):
    if not app.debug:
        sentry_sdk.init(
            dsn=os.environ.get('SENTRY_SDK_DSN'),
            integrations=[
                FlaskIntegration(),
            ],
            send_default_pii=True,
            traces_sample_rate=1.0
        )
