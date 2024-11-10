import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH")) * 1 * 1024 # 1 MB
    
    # Database configuration
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "sslmode": "require"
        }
    }

    # Email SMTP
    MAIL_SERVER=os.getenv('MAIL_SERVER')
    MAIL_PORT=os.getenv('MAIL_PORT')
    MAIL_USE_TLS=os.getenv('MAIL_USE_TLS')
    MAIL_USERNAME=os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER=('Campsite App', 'nathancp93@gmail.com')
    SITE_URL=os.getenv('SITE_URL')