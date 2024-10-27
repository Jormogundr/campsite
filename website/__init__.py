import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv


load_dotenv()

# database
db = SQLAlchemy()
db_name = os.getenv("DB_NAME")
db_url = os.getenv("DATABASE_URL")
db_pw = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")

# SQLAlchemy prefix requires replacement: https://stackoverflow.com/questions/62688256/sqlalchemy-exc-nosuchmoduleerror-cant-load-plugin-sqlalchemy-dialectspostgre
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# media
max_file_sz = os.getenv("MAX_CONENT_LENGTH")

# secrets
secret_key = os.getenv("SECRET_KEY")

migrate = Migrate()

def create_app():
    # production db
    app = Flask(__name__)
    app.config["SECRET_KEY"] = secret_key
    app.config["MAX_CONENT_LENGTH"] = max_file_sz
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    
    # ssl required by heroku, the other vars are supplied in heroku env, only include for local debugging
    # sqlalchemy engine configuration keys https://flask-sqlalchemy.palletsprojects.com/en/2.x/config/
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": dict(
            sslmode="require",
            # username=db_user,
            # password=db_pw,
            # host=db_host,

        )
    }

    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = SQLALCHEMY_ENGINE_OPTIONS
    
    db.init_app(app)
    migrate.init_app(app, db)

    from .views.views import views
    from .auth import auth

    # Blueprints TODO Remove this, since we are using our own MVC to organize the project
    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")

    from .models.models import User

    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app


def create_database(app):
    if not os.path.exists("website/" + db_name):
        db.create_all(app=app)
        print("Created Database!")
