from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from config import GRINDER_SETTINGS, SHOT_SETTINGS
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
import re

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    
    @staticmethod
    def validate_password(password):
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", password):
            raise ValueError("Password must contain at least one number")
        return True
    
    def set_password(self, password):
        self.validate_password(password)
        self.password = generate_password_hash(password)

class GrinderSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_grinder_settings_user'), nullable=False)
    grinder_type = db.Column(db.String(20), default='stepped')  # Add this line
    min_size = db.Column(db.Float, nullable=False, default=0)
    max_size = db.Column(db.Float, nullable=False, default=50)
    step_size = db.Column(db.Float, nullable=False, default=0.25)
    last_used_size = db.Column(db.Float)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, user_id):
        self.user_id = user_id
        self.min_size = GRINDER_SETTINGS['MIN_SIZE']['default']
        self.max_size = GRINDER_SETTINGS['MAX_SIZE']['default']
        self.step_size = GRINDER_SETTINGS['STEP_SIZE']['default']

class Coffee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_coffee_user'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    roaster = db.Column(db.String(100), nullable=False)
    roast_date = db.Column(db.Date, nullable=False)
    tasting_notes = db.Column(db.Text)
    grams = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Coffee {self.name} by {self.roaster}>'

class Shot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    coffee_id = db.Column(db.Integer, db.ForeignKey('coffee.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    grind_size = db.Column(db.Float, nullable=False)
    coffee_weight = db.Column(db.Float, nullable=False)
    shot_time = db.Column(db.Float, nullable=False)
    shot_yield = db.Column(db.Float, nullable=False)
    taste = db.Column(db.Integer, nullable=False)
    body = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)
    
    coffee = db.relationship('Coffee', backref='shots')

    def __repr__(self):
        return f'<Shot {self.id}>'

    def __init__(self, **kwargs):
        super(Shot, self).__init__(**kwargs)
        if not 0 <= self.grind_size <= 50:
            raise ValueError("Grind size must be between 0 and 50")
        if not 0 < self.coffee_weight <= 30:
            raise ValueError("Coffee weight must be between 0 and 30 grams")
        if not 0 < self.shot_yield <= 100:
            raise ValueError("Shot yield must be between 0 and 100 grams")
        if not 0 <= self.taste <= 100:
            raise ValueError("Invalid shot taste value")
        if not 0 <= self.body <= 100:
            raise ValueError("Invalid shot body value")

    @classmethod
    def get_user_stats(cls, user_id):
        """Get statistics for a user's shots."""
        today = datetime.now().date()
        return {
            'today_shots_count': cls.query.filter(
                cls.user_id == user_id,
                cls.date >= today
            ).count(),
            'total_shots_count': cls.query.filter_by(user_id=user_id).count(),
            'avg_rating': db.session.query(
                func.avg(cls.taste)
            ).filter_by(user_id=user_id).scalar() or 0
        }