from flask import Flask, jsonify
from flask_cors import CORS
from app.extensions import db, jwt, migrate
from app.config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    """Application Factory Pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    with app.app_context():
        # Ensure models are imported so SQLAlchemy can create tables
        from app.models import school, user, role, permission, student, activity, parent, staff

        # Create tables if they don't exist
        db.create_all()
        
        # Register blueprints
        from app.routes.auth_routes import auth_bp
        from app.routes.student_routes import student_bp
        from app.routes.parent_routes import parent_bp
        from app.routes.staff_routes import staff_bp
        from app.routes.dashboard_routes import dashboard_bp
        
        app.register_blueprint(auth_bp, url_prefix="/api")
        app.register_blueprint(student_bp, url_prefix="/api")
        app.register_blueprint(parent_bp, url_prefix="/api")
        app.register_blueprint(staff_bp, url_prefix="/api")
        app.register_blueprint(dashboard_bp, url_prefix="/api")
        
        # ADDED: A friendly health-check route for the root URL
        @app.route('/')
        def index():
            return jsonify({
                "status": "online",
                "message": "School Management System API is running. Access the UI at http://localhost:8000"
            }), 200
        
        logger.info("Application initialized successfully")
    
    return app