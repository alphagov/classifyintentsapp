from flask import Flask
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_pagedown import PageDown

bootstrap = Bootstrap()
moment = Moment()
db = SQLAlchemy()
pagedown = PageDown()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'


def create_app(config_name):
    app = Flask(__name__)
    # import config here rather than at module level to ensure that .env values
    # are loaded into the environment first when running manage.py
    from config import config
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)

    # Set jquery version
    from flask_bootstrap import WebCDN
    app.extensions['bootstrap']['cdns']['jquery'] = WebCDN(
        '//cdnjs.cloudflare.com/ajax/libs/jquery/3.2.1/'
    )

    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)

    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask_sslify import SSLify
        sslify = SSLify(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    # Tell browser not to cache any HTML responses, as most pages have
    # sensitive information in them. (But CSS should be cached as normal.)
    @app.after_request
    def apply_caching(response):
        if response.headers.get('Content-Type', '').startswith('text/html'):
            response.headers['Cache-control'] = 'no-store'
            response.headers['Pragma'] = 'no-cache'
        return response

    return app
