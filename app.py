from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from models import db, User
from config import (
    SQLALCHEMY_DATABASE_URI,
    GRINDER_SETTINGS,
    SHOT_SETTINGS,
    COFFEE_SETTINGS,
    SECURITY_HEADERS,
    SESSION_COOKIE_SECURE,
    SESSION_COOKIE_HTTPONLY,
    SESSION_COOKIE_SAMESITE
)
import os

# Initialize extensions
login_manager = LoginManager()
migrate = Migrate()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_db(app):
    with app.app_context():
        db.create_all()
        try:
            migrate.init_app(app, db)
        except Exception as e:
            print(f"Migration error: {e}")

def create_app():
    app = Flask(__name__)
    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Security configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    
    # Session configuration
    is_production = os.environ.get('FLASK_ENV') == 'production'
    app.config['SESSION_COOKIE_SECURE'] = is_production
    app.config['SESSION_COOKIE_HTTPONLY'] = SESSION_COOKIE_HTTPONLY
    app.config['SESSION_COOKIE_SAMESITE'] = SESSION_COOKIE_SAMESITE
    
    # Application settings
    app.config['GRINDER_SETTINGS'] = GRINDER_SETTINGS
    app.config['SHOT_SETTINGS'] = SHOT_SETTINGS
    app.config['COFFEE_SETTINGS'] = COFFEE_SETTINGS
    
    # Initialize extensions with app
    db.init_app(app)
    init_db(app)
    login_manager.init_app(app)
    
    # Initialize Talisman without forcing HTTPS
    Talisman(app, content_security_policy=None, force_https=False)
    
    # Initialize Limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    
    login_manager.login_view = 'login'
    login_manager.session_protection = 'strong'
    
    @app.after_request
    def add_security_headers(response):
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        return response
    
    from routes import init_routes
    init_routes(app, limiter)
    
    return app

# Create the app instance outside of main
app = create_app()

if __name__ == '__main__':
    app.run(debug=False)
