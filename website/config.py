import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    
    # Database configuration
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL:
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        if "?" not in DATABASE_URL:
            DATABASE_URL += "?sslmode=require"
        elif "sslmode=" not in DATABASE_URL:
            DATABASE_URL += "&sslmode=require"
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,  # Enables automatic reconnection
        "pool_recycle": 300,    # Recycle connections every 5 minutes
        "pool_timeout": 30,     # Connection timeout after 30 seconds
        "pool_size": 5,         # Maximum number of persistent connections
        "max_overflow": 10      # Maximum number of connections that can be created beyond pool_size
        #"sslmode": "require"
    }

    # Email SMTP
    MAIL_SERVER=os.getenv('MAIL_SERVER')
    MAIL_PORT=os.getenv('MAIL_PORT')
    MAIL_USE_TLS=os.getenv('MAIL_USE_TLS')
    MAIL_USERNAME=os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER=('Campsite App', 'nathancp93@gmail.com')
    SITE_URL=os.getenv('SITE_URL')

    # Photos
    CAMPSITE_PHOTO_UPLOAD_PATH = os.getenv("CAMPSITE_PHOTO_UPLOAD_PATH")
    PROFILE_PHOTO_UPLOAD_PATH = os.getenv("PROFILE_PHOTO_UPLOAD_PATH")
    ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH")) * 1 * 1024 # 1 MB
