from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import pymysql
import urllib.parse
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from logging.handlers import RotatingFileHandler
import logging
import locale
from flask_cors import CORS
from flask_wtf import CSRFProtect  # Import CSRFProtect
from flask_migrate import Migrate


# Initialize extensions globally
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()  # Initialize CSRFProtect
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri='redis://localhost:6379/0'  # Redis URL for rate limiter storage
)

def create_app():
    app = Flask(__name__)

   


    # Load configurations
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = urllib.parse.quote(os.environ.get('MYSQL_PASSWORD', 'password'))
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_NAME = os.environ.get('DB_NAME', 'credentials')
    DB_NAME_TONERS = os.environ.get('DB_NAME_TONERS', 'toners')
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'your_default_secret_key')
    UPLOAD_FOLDER = '\static\SPAPHOTOS'  # Use a relative path for the upload folder
    
    # Directly set the upload folder path without using an environment variable
   
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    
    ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'webp'])
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

  

    app.config.update(
        SECRET_KEY=SECRET_KEY,
        DEBUG=os.environ.get('FLASK_DEBUG', 'false').lower() in ['true', '1', 't', 'y', 'yes'],
        SQLALCHEMY_DATABASE_URI=f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}',
        SQLALCHEMY_BINDS={
            'toners': f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME_TONERS}'
        },
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_SECURE=not app.debug,  # Set to True only in production
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Strict',
        CSRF_ENABLED=True,  # Enable CSRF protection
        CSRF_COOKIE_SECURE=not app.debug,  # Set to True only in production
        CSRF_COOKIE_SAMESITE='Strict'
    )

    # Set up logging
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    if not app.debug:
        # Production environment
        file_handler = RotatingFileHandler('app.log', maxBytes=100000, backupCount=1)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        app.logger.addHandler(file_handler)
    else:
        # Development environment
        handler.setLevel(logging.DEBUG)
        app.logger.addHandler(handler)
    
    app.logger.setLevel(logging.DEBUG)

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    csrf.init_app(app)  # Initialize CSRFProtect
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    limiter.init_app(app)  # Initialize rate limiter

    # Enable CORS with credentials support
    CORS(app, supports_credentials=True)

    # Import blueprints and register them
    from .views import views
    from .auth import auth
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # Import models and create database tables
    from .models import User, Note, LoanRecord
    
    with app.app_context():
        db.create_all()

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Set locale for currency formatting
    locale.setlocale(locale.LC_ALL, '')

    def currency(value):
        try:
            return locale.currency(value, grouping=True)
        except (ValueError, TypeError):
            return value

    # Register the custom currency filter
    app.jinja_env.filters['currency'] = currency
    
    return app