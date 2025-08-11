from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config
# from flask_moment import Moment

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

# moment = Moment()

# def create_app():
#     app = Flask(__name__)
#     moment.init_app(app)
#     return app


csrf = CSRFProtect()

# def create_app():
#     app = Flask(__name__)
#     moment.init_app(app)
#     return app

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes.main_routes import main_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.patient_routes import patient_bp
    from app.routes.hospital_routes import hospital_bp
    from app.routes.host_routes import host_bp
    from app.routes.admin_routes import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(patient_bp, url_prefix='/patient')
    app.register_blueprint(hospital_bp, url_prefix='/hospital')
    app.register_blueprint(host_bp, url_prefix='/host')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # ✅ Inject CSRF token into Jinja templates for manual HTML forms
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf())

    return app
