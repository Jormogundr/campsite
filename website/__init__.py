import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv


# load env vars
load_dotenv()

#database 
db = SQLAlchemy()
db_name = os.getenv("DB_NAME")
db_url = os.getenv("DATABASE_URL")

# media
max_file_sz = os.getenv("MAX_CONENT_LENGTH")

# secrets
secret_key = os.getenv("SECRET_KEY")

# for local testing
DB_NAME = "test14.db"


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = secret_key
    app.config['MAX_CONENT_LENGTH'] = max_file_sz

    # production db
    # app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:////home/nate/{DB_NAME}'
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, CampSite
    
    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app


def create_database(app):
    if not os.path.exists('website/' + db_name):
        db.create_all(app=app)
        print('Created Database!')
