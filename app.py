from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from config import SQLALCHEMY_DATABASE_URI
from models import db, User
from config import (
    SQLALCHEMY_DATABASE_URI, 
    GRINDER_SETTINGS, 
    SHOT_SETTINGS,
    COFFEE_SETTINGS
)

login_manager = LoginManager()
migrate = Migrate()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your-secret-key'
    
    # Add settings
    app.config['GRINDER_SETTINGS'] = GRINDER_SETTINGS
    app.config['SHOT_SETTINGS'] = SHOT_SETTINGS
    app.config['COFFEE_SETTINGS'] = COFFEE_SETTINGS
    
    # Initialize the app with SQLAlchemy, LoginManager, and Migrate
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    login_manager.login_view = 'login'
    
    from routes import init_routes
    init_routes(app)
    
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
