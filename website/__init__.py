from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import pymysql
pymysql.install_as_MySQLdb()
import urllib.parse

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

DB_USER = 'root'
DB_PASSWORD = urllib.parse.quote('chronnix@123')
DB_HOST = 'localhost'
DB_NAME = 'credentials'
DB_NAME_TONERS = 'toners'

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'
    app.config['DEBUG'] = True  # Enable debug mode
    
    
    # Update the URI for MySQL
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
    app.config['SQLALCHEMY_BINDS'] = {
    'toners': f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME_TONERS}'
    }
    
    db.init_app(app)
    
    # Initialize LoginManager
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    # Import blueprints
    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # Import models
    from .models import User, Note, LoanRecord
    
    # Create database table
    with app.app_context():
        db.create_all()
        

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    return app