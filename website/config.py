# config.py
import os
from dotenv import load_dotenv
from scripts import make_secrets

load_dotenv()

class Config:
    # Class-level attributes for direct access
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_timeout": 30,
        "pool_size": 5,
        "max_overflow": 10
    }

    # Email SMTP
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = os.getenv('MAIL_PORT')
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ('Campsite App', 'nathancp93@gmail.com')
    SITE_URL = os.getenv('SITE_URL')

    # Photos
    CAMPSITE_PHOTO_UPLOAD_PATH = os.getenv("CAMPSITE_PHOTO_UPLOAD_PATH")
    PROFILE_PHOTO_UPLOAD_PATH = os.getenv("PROFILE_PHOTO_UPLOAD_PATH")
    ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH")) * 1 * 1024

    def __init__(self, is_production=False):
        # Copy all class attributes to instance
        for attr in dir(self):
            if not attr.startswith('__'):
                setattr(self, attr, getattr(self, attr))
        
        # Set database URI based on production flag
        if is_production:
            DATABASE_URL = os.getenv("DATABASE_URL")
            if DATABASE_URL:
                if DATABASE_URL.startswith("postgres://"):
                    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
                if "?" not in DATABASE_URL:
                    DATABASE_URL += "?sslmode=require"
                elif "sslmode=" not in DATABASE_URL:
                    DATABASE_URL += "&sslmode=require"
            self.SQLALCHEMY_DATABASE_URI = DATABASE_URL
        else:
            self.SQLALCHEMY_DATABASE_URI = 'sqlite:///dev.db'
            self.SECRET_KEY = make_secrets.generate_secret_key()