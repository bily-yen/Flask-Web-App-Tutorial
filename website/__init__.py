from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO  # Import SocketIO
import pymysql
import urllib.parse
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from logging.handlers import RotatingFileHandler
import logging
import locale
from flask_cors import CORS
from flask_wtf import CSRFProtect
from flask_migrate import Migrate
from flask_mail import Mail
from dotenv import load_dotenv  # Import the dotenv package

# Load environment variables from .env file
load_dotenv()  # This loads the variables from the .env file into the environment

# Initialize extensions globally
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri='redis://localhost:6379/0'
)
socketio = SocketIO()  # Initialize SocketIO
mail = Mail()  # Initialize Flask-Mail

def create_app():
    app = Flask(__name__)

    # Ensure all necessary environment variables are present or raise an error
    DB_USER = os.getenv('DB_USER')
    if not DB_USER:
        raise ValueError("Missing environment variable: DB_USER")
    
    DB_PASSWORD = urllib.parse.quote(os.getenv('MYSQL_PASSWORD'))
    if not DB_PASSWORD:
        raise ValueError("Missing environment variable: MYSQL_PASSWORD")

    DB_HOST = os.getenv('DB_HOST')
    if not DB_HOST:
        raise ValueError("Missing environment variable: DB_HOST")

    DB_NAME = os.getenv('DB_NAME')
    if not DB_NAME:
        raise ValueError("Missing environment variable: DB_NAME")

    DB_NAME_TONERS = os.getenv('DB_NAME_TONERS')
    if not DB_NAME_TONERS:
        raise ValueError("Missing environment variable: DB_NAME_TONERS")

    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("Missing environment variable: FLASK_SECRET_KEY")

    MAIL_SERVER = os.getenv('MAIL_SERVER')
    if not MAIL_SERVER:
        raise ValueError("Missing environment variable: MAIL_SERVER")

    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    if not MAIL_USERNAME:
        raise ValueError("Missing environment variable: MAIL_USERNAME")

    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    if not MAIL_PASSWORD:
        raise ValueError("Missing environment variable: MAIL_PASSWORD")

    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    if not MAIL_DEFAULT_SENDER:
        raise ValueError("Missing environment variable: MAIL_DEFAULT_SENDER")

    # Use booleans for MAIL_USE_TLS and MAIL_USE_SSL
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'False') == 'True'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'True') == 'True'

    # Set file upload configurations
    UPLOAD_FOLDER = r'static\SPAPHOTOS'  # Use a relative path for the upload folder
    
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    
    ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'webp'])
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    # General configurations
    app.config.update(
        SECRET_KEY=SECRET_KEY,  # Secret key loaded from environment variable
        DEBUG=os.getenv('FLASK_DEBUG', 'false').lower() in ['true', '1', 't', 'y', 'yes'],
        SQLALCHEMY_DATABASE_URI=f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}',
        SQLALCHEMY_BINDS={
            'toners': f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME_TONERS}'
        },
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_SECURE=not app.debug,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Strict',
        CSRF_ENABLED=True,
        CSRF_COOKIE_SECURE=not app.debug,
        CSRF_COOKIE_SAMESITE='Strict',

        # SMTP Configuration for Flask-Mail (using environment variables)
        MAIL_SERVER=MAIL_SERVER,
        MAIL_PORT=int(os.getenv('MAIL_PORT', 465)),
        MAIL_USE_TLS=MAIL_USE_TLS,
        MAIL_USE_SSL=MAIL_USE_SSL,
        MAIL_USERNAME=MAIL_USERNAME,
        MAIL_PASSWORD=MAIL_PASSWORD,
        MAIL_DEFAULT_SENDER=MAIL_DEFAULT_SENDER,
    )

    # Set up logging
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    if not app.debug:
        file_handler = RotatingFileHandler('app.log', maxBytes=100000, backupCount=1)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        app.logger.addHandler(file_handler)
    else:
        handler.setLevel(logging.DEBUG)
        app.logger.addHandler(handler)
    
    app.logger.setLevel(logging.DEBUG)

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    csrf.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    limiter.init_app(app)
    
    # Initialize SocketIO with the Flask app
    socketio.init_app(app)  # Initialize SocketIO

    # Initialize Flask-Mail with the app
    mail.init_app(app)

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
    
    return app, socketio  # Return both app and socketio
