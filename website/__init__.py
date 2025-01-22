import os
import urllib.parse
import locale
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO
from logging.handlers import RotatingFileHandler

# Initialize extensions globally
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, storage_uri='redis://localhost:6379/0')
socketio = SocketIO()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # Configuration
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = urllib.parse.quote_plus(os.environ.get('MYSQL_PASSWORD', 'chronnix@123'))
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_NAME = os.environ.get('DB_NAME', 'topa')
    DB_NAME_TONERS = os.environ.get('DB_NAME_TONERS', 'toners')
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))
    UPLOAD_FOLDER = r'static\SPAPHOTOS'

    app.config.update(
        SECRET_KEY=SECRET_KEY,
        SQLALCHEMY_DATABASE_URI=f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}',
        SQLALCHEMY_BINDS={
            'toners': f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME_TONERS}'
        },
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=UPLOAD_FOLDER,
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
        SESSION_COOKIE_SECURE=not app.debug,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Strict',
        CSRF_ENABLED=True,
    )

    # Logging
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    app.logger.addHandler(handler)
    if not app.debug:
        file_handler = RotatingFileHandler('app.log', maxBytes=100000, backupCount=1)
        file_handler.setFormatter(handler.formatter)
        app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.DEBUG)

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)
    CORS(app, supports_credentials=True)

    # Register blueprints
    from .views import views
    from .auth import auth
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # Import models
    from .models import User, Note, LoanRecord
    with app.app_context():
        db.create_all()

    # Login user loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Locale setup
    try:
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error as e:
        app.logger.warning(f"Locale could not be set: {e}")

    def currency(value):
        try:
            return locale.currency(value, grouping=True)
        except (ValueError, TypeError):
            return value

    app.jinja_env.filters['currency'] = currency

    return app, socketio