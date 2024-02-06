import os
from redis import Redis
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file if present

class Config:
    # Assuming your config.py is at the root of your Flask application
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # Directory of config.py
    # Point to the 'chat.db' inside the 'instance' directory relative to the location of this file
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'chat.db'))
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///chat.db'
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_TYPE = 'redis'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'session:'
    # SESSION_REDIS = 'redis://localhost:6379'
    SESSION_REDIS = Redis(host='localhost', port=6379)
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './data/card')
    ALLOWED_EXTENSIONS = {'png'}
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 16MB limit to prevent large uploads
    
    # Add any other configuration variables that you use
