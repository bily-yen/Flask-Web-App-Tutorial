from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import pymysql
import urllib.parse
import os
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from logging.handlers import RotatingFileHandler
import logging
import locale

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)

    # Load configurations from environment variables
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = urllib.parse.quote(os.environ.get('MYSQL_PASSWORD', 'password'))
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_NAME = os.environ.get('DB_NAME', 'credentials')
    DB_NAME_TONERS = os.environ.get('DB_NAME_TONERS', 'toners')
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'your_default_secret_key')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')

    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'false').lower() in ['true', '1', 't', 'y', 'yes']
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
    app.config['SQLALCHEMY_BINDS'] = {
        'toners': f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME_TONERS}'
    }
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
    
    db.init_app(app)
    
    # Initialize extensions
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    csrf.init_app(app)

    # Set up file logging
    if not app.debug:
        handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
    
    # Initialize Flask-Limiter
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=f'redis://localhost:6379/0'  # Redis URL for rate limiter storage
    )
    limiter.init_app(app)

    # Import blueprints
    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # Import models
    from .models import User, Note, LoanRecord
    
    # Create database tables
    with app.app_context():
        db.create_all()

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    locale.setlocale(locale.LC_ALL, '')

    def currency(value):
        try:
            return locale.currency(value, grouping=True)
        except (ValueError, TypeError):
            return value

    # Register the custom currency filter
    app.jinja_env.filters['currency'] = currency
    
    return app