import os

from flask import Flask
from .config import Config
from .extensions import db, migrate, login_manager, socketio, mail
from .models.models import User

from dotenv import load_dotenv
load_dotenv() 

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    mail.init_app(app)
    
    # Configure login
    login_manager.login_view = "auth.login"
    
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    # Register blueprints
    from .views.home import home_bp
    from .views.add_campsite import add_campsite_bp
    from .views.view_campsite import view_campsite_bp
    from .views.profile import profile_bp
    from .views.campsite_list import campsite_lists_bp
    from .views.search import search_bp
    
    app.register_blueprint(home_bp, url_prefix="/")
    app.register_blueprint(add_campsite_bp, url_prefix="/add-campsite/")
    app.register_blueprint(view_campsite_bp, url_prefix="/campsites/")
    app.register_blueprint(profile_bp, url_prefix="/profile/")
    app.register_blueprint(campsite_lists_bp, url_prefix="/campsite-lists/")
    app.register_blueprint(search_bp, url_prefix="/search/")

    from .auth import auth
    app.register_blueprint(auth, url_prefix="/")
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

def create_database(app):
    if not os.path.exists("website/" + os.getenv("DB_NAME")):
        with app.app_context():
            db.create_all()
            print("Created Database!")