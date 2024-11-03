import os

from flask import Flask
from .config import Config
from .extensions import db, migrate, login_manager, socketio
from .models.models import User

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Configure login
    login_manager.login_view = "auth.login"
    
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    # Register blueprints
    from .views.views import views
    from .auth import auth
    
    app.register_blueprint(views, url_prefix="/")
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