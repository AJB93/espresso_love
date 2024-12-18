import os
from dotenv import load_dotenv

load_dotenv()

# Base Configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'database.db')

# Security Configuration
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("No SECRET_KEY set in environment variables")

# Database Configuration
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///espresso.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Security Headers
SECURITY_HEADERS = {
    'STRICT_TRANSPORT_SECURITY': 'max-age=31536000; includeSubDomains',
    'X_CONTENT_TYPE_OPTIONS': 'nosniff',
    'X_FRAME_OPTIONS': 'SAMEORIGIN',
    'X_XSS_PROTECTION': '1; mode=block',
}

# Session Configuration
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Grinder Settings Validation
GRINDER_SETTINGS = {
    'GRINDER_TYPE': {
        'options': ['stepped', 'stepless'],
        'default': 'stepped'
    },
    'MIN_SIZE': {
        'min': 0,
        'max': 50,
        'default': 0,
        'step': 0.1,
    },
    'MAX_SIZE': {
        'min': 0,
        'max': 100,
        'default': 50,
        'step': 0.1,
    },
    'STEP_SIZE': {
        'min': 0.01,
        'max': 1,
        'default': 0.25,
        'step': 0.01,
    }
}

# Shot Parameters Settings
SHOT_SETTINGS = {
    'DOSE': {
        'min': 0,
        'max': 100,
        'default': 18,
        'step': 0.1,
        'unit': 'g'
    },
    'SHOT_TIME': {
        'min': 0,
        'max': 180,
        'default': 30,
        'step': 1,
        'unit': 's'
    },
    'SHOT_YIELD': {
        'min': 0,
        'max': 200,
        'default': 32,
        'step': 0.1,
        'unit': 'g'
    }
}

# Add to existing config.py
COFFEE_SETTINGS = {
    'GRAMS': {
        'min': 0,
        'max': 1000,
        'default': 250,
        'step': 1,
        'unit': 'g'
    }
}
