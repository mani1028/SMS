from flask import Flask, jsonify
from app.extensions import db, jwt
from app.config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    """Application Factory Pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Register blueprints
        from app.routes.auth_routes import auth_bp
        from app.routes.student_routes import student_bp
        
        app.register_blueprint(auth_bp, url_prefix="/api")
        app.register_blueprint(student_bp, url_prefix="/api")
        
        # ADDED: A friendly health-check route for the root URL
        @app.route('/')
        def index():
            return jsonify({
                "status": "online",
                "message": "School Management System API is running. Access the UI at http://localhost:8000"
            }), 200
        
        logger.info("Application initialized successfully")
    
    return app