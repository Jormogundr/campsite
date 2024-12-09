import os

from flask import Flask, render_template
from flask_login import current_user
from werkzeug.exceptions import HTTPException

from .config import Config
from .extensions import db, migrate, login_manager, socketio, mail
from .models.models import User

from dotenv import load_dotenv
load_dotenv() 

def create_app(is_production=False):
    is_production = os.getenv('FLASK_ENV', 'false').lower() == 'production'
    print(f"Running in mode: {'PRODUCTION' if is_production else 'DEVELOPMENT'}")
    
    app = Flask(__name__)
    app.config.from_object(Config(is_production=is_production))
    
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

    # Register authentication
    from .auth import auth
    app.register_blueprint(auth, url_prefix="/")

    # Error handling
    register_error_handling(app)

    # For local testing only
    FILL_TABLES = os.getenv("FILL_TABLES")
    if FILL_TABLES:
        from .test.filltables import fill_table_bp
        app.register_blueprint(fill_table_bp, url_prefix="/filltables")
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

def create_database(app):
    if not os.path.exists("website/" + os.getenv("DB_NAME")):
        with app.app_context():
            db.create_all()
            print("Created Database!")

def register_error_handling(app):
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html', 
                             error_code=404,
                             user=current_user,
                             msg="The page you're looking for doesn't exist."), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('error.html',
                             error_code=500,
                             user=current_user,
                             msg="Something went wrong on our end. Please try again later."), 500

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('error.html',
                             error_code=403,
                             user=current_user,
                             msg="You don't have permission to access this resource."), 403

    # Catch-all exception handler
    @app.errorhandler(Exception)
    def handle_exception(e):
        # Pass through HTTP errors
        if isinstance(e, HTTPException):
            return render_template('error.html',
                                error_code=e.code,
                                user=current_user,
                                msg=e.description), e.code
        
        # Log non-HTTP exceptions
        app.logger.error(f'Unhandled exception: {str(e)}')
        return render_template('error.html',
                             error_code=500,
                             user=current_user,
                             msg="An unexpected error occurred."), 500
