import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'database.db')
SQLALCHEMY_DATABASE_URI = 'sqlite:///espresso.db'
SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-temporary-key'

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
