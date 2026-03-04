from flask import Flask, jsonify, request
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
        # Import SMS module models
        from app.models import academics, attendance, exams, finance, logistics, communication, settings
        # Import CRM models
        from app.models import enquiry
        # Import SaaS models
        from app.models import billing
        # Import new feature models
        from app.models import branch, alert, advanced
        # Import Phase 2 feature models
        from app.models import expense, curriculum, feature_toggle
        from app.services.backup_service import BackupRecord

        # Create tables if they don't exist
        db.create_all()
        
        # Auto-seed plans and super admin on first run
        from app.models.billing import Plan
        from app.models.user import User
        
        if Plan.query.count() == 0:
            # Create default subscription plans
            plans_data = [
                {'name': 'Free', 'price_monthly': 0, 'price_annual': 0, 'max_students': 100, 'max_staff': 10, 'storage_gb': 5, 'sms_credits_monthly': 100, 'api_calls_per_day': 1000, 'display_order': 1},
                {'name': 'Basic', 'price_monthly': 499, 'price_annual': 4990, 'max_students': 500, 'max_staff': 50, 'storage_gb': 50, 'sms_credits_monthly': 1000, 'api_calls_per_day': 10000, 'display_order': 2},
                {'name': 'Pro', 'price_monthly': 1299, 'price_annual': 12990, 'max_students': 2000, 'max_staff': 200, 'storage_gb': 200, 'sms_credits_monthly': 5000, 'api_calls_per_day': 50000, 'display_order': 3},
                {'name': 'Enterprise', 'price_monthly': 4999, 'price_annual': 49990, 'max_students': 10000, 'max_staff': 500, 'storage_gb': 1000, 'sms_credits_monthly': 50000, 'api_calls_per_day': 500000, 'display_order': 4},
            ]
            for plan_data in plans_data:
                plan = Plan(**plan_data)
                db.session.add(plan)

        # Create super admin user
        if User.query.filter_by(email='admin@platform.local').count() == 0:
            admin = User(
                name='Platform Admin',
                email='admin@platform.local',
                is_active=True,
                is_super_admin=True,
                school_id=None
            )
            admin.set_password('Admin@123456')
            db.session.add(admin)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.warning(f"Auto-seed skipped due to schema mismatch: {e}")
        
        # Register blueprints - Original routes
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
        
        # Register blueprints - New SMS modules
        try:
            from app.routes.academics_routes import academic_bp
            app.register_blueprint(academic_bp, url_prefix="/api")
            logger.info("✓ Academics routes registered")
        except Exception as e:
            logger.warning(f"Academics routes not available: {e}")
        
        try:
            from app.routes.attendance_routes import attendance_bp
            app.register_blueprint(attendance_bp, url_prefix="/api")
            logger.info("✓ Attendance routes registered")
        except Exception as e:
            logger.warning(f"Attendance routes not available: {e}")
        
        try:
            from app.routes.exams_routes import exam_bp
            app.register_blueprint(exam_bp, url_prefix="/api")
            logger.info("✓ Exams routes registered")
        except Exception as e:
            logger.warning(f"Exams routes not available: {e}")
        
        try:
            from app.routes.finance_routes import finance_bp
            app.register_blueprint(finance_bp, url_prefix="/api")
            logger.info("✓ Finance routes registered")
        except Exception as e:
            logger.warning(f"Finance routes not available: {e}")
        
        try:
            from app.routes.logistics_routes import logistics_bp
            app.register_blueprint(logistics_bp, url_prefix="/api")
            logger.info("✓ Logistics routes registered")
        except Exception as e:
            logger.warning(f"Logistics routes not available: {e}")
        
        try:
            from app.routes.communication_routes import communication_bp
            app.register_blueprint(communication_bp, url_prefix="/api")
            logger.info("✓ Communication routes registered")
        except Exception as e:
            logger.warning(f"Communication routes not available: {e}")
        
        try:
            from app.routes.settings_routes import settings_bp
            app.register_blueprint(settings_bp, url_prefix="/api")
            logger.info("✓ Settings routes registered")
        except Exception as e:
            logger.warning(f"Settings routes not available: {e}")
        
        # Register CRM routes
        try:
            from app.routes.enquiry_routes import enquiry_bp
            app.register_blueprint(enquiry_bp, url_prefix="/api")
            logger.info("✓ Enquiry routes registered")
        except Exception as e:
            logger.warning(f"Enquiry routes not available: {e}")
        
        # Register test routes
        try:
            from app.routes.test_routes import test_bp
            app.register_blueprint(test_bp, url_prefix="/api")
            logger.info("✓ Test routes registered")
        except Exception as e:
            logger.warning(f"Test routes not available: {e}")
        
        # Register Platform (SaaS) routes
        try:
            from app.routes.platform_routes import platform_bp
            app.register_blueprint(platform_bp, url_prefix="/api")
            logger.info("✓ Platform routes registered")
        except Exception as e:
            logger.warning(f"Platform routes not available: {e}")
        
        # Register Analytics routes
        try:
            from app.routes.analytics_routes import analytics_bp
            app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
            logger.info("✓ Analytics routes registered")
        except Exception as e:
            logger.warning(f"Analytics routes not available: {e}")
        
        # Register Audit routes
        try:
            from app.routes.audit_routes import audit_bp
            app.register_blueprint(audit_bp, url_prefix="/api/audit")
            logger.info("✓ Audit routes registered")
        except Exception as e:
            logger.warning(f"Audit routes not available: {e}")
        
        # Register Parent Portal routes
        try:
            from app.routes.parent_portal_routes import parent_portal_bp
            app.register_blueprint(parent_portal_bp, url_prefix="/api/parent-portal")
            logger.info("✓ Parent Portal routes registered")
        except Exception as e:
            logger.warning(f"Parent Portal routes not available: {e}")
        
        # Register Payment Gateway routes
        try:
            from app.routes.payment_routes import payment_bp
            app.register_blueprint(payment_bp, url_prefix="/api/payments")
            logger.info("✓ Payment Gateway routes registered")
        except Exception as e:
            logger.warning(f"Payment Gateway routes not available: {e}")
        
        # Register Alert routes
        try:
            from app.routes.alert_routes import alert_bp
            app.register_blueprint(alert_bp, url_prefix="/api/alerts")
            logger.info("✓ Alert routes registered")
        except Exception as e:
            logger.warning(f"Alert routes not available: {e}")
        
        # Register Branch routes
        try:
            from app.routes.branch_routes import branch_bp
            app.register_blueprint(branch_bp, url_prefix="/api/branches")
            logger.info("✓ Branch routes registered")
        except Exception as e:
            logger.warning(f"Branch routes not available: {e}")
        
        # Register Advanced Feature routes (ID Cards, Promotions, Documents, API Keys, Reports)
        try:
            from app.routes.advanced_routes import advanced_bp
            app.register_blueprint(advanced_bp, url_prefix="/api/advanced")
            logger.info("✓ Advanced Feature routes registered")
        except Exception as e:
            logger.warning(f"Advanced Feature routes not available: {e}")
        
        # Register Bulk Operations routes
        try:
            from app.routes.bulk_routes import bulk_bp
            app.register_blueprint(bulk_bp, url_prefix="/api/bulk")
            logger.info("✓ Bulk Operations routes registered")
        except Exception as e:
            logger.warning(f"Bulk Operations routes not available: {e}")
        
        # Register Expense Management routes
        try:
            from app.routes.expense_routes import expense_bp
            app.register_blueprint(expense_bp, url_prefix="/api/expenses")
            logger.info("✓ Expense Management routes registered")
        except Exception as e:
            logger.warning(f"Expense Management routes not available: {e}")
        
        # Register Curriculum Planner routes
        try:
            from app.routes.curriculum_routes import curriculum_bp
            app.register_blueprint(curriculum_bp, url_prefix="/api/curriculum")
            logger.info("✓ Curriculum Planner routes registered")
        except Exception as e:
            logger.warning(f"Curriculum Planner routes not available: {e}")
        
        # Register Backup & Restore routes
        try:
            from app.routes.backup_routes import backup_bp
            app.register_blueprint(backup_bp, url_prefix="/api/backups")
            logger.info("✓ Backup & Restore routes registered")
        except Exception as e:
            logger.warning(f"Backup & Restore routes not available: {e}")
        
        # Register Custom Branding routes
        try:
            from app.routes.branding_routes import branding_bp
            app.register_blueprint(branding_bp, url_prefix="/api/branding")
            logger.info("✓ Custom Branding routes registered")
        except Exception as e:
            logger.warning(f"Custom Branding routes not available: {e}")
        
        # Register Feature Toggle routes
        try:
            from app.routes.feature_toggle_routes import feature_toggle_bp
            app.register_blueprint(feature_toggle_bp, url_prefix="/api/features")
            logger.info("✓ Feature Toggle routes registered")
        except Exception as e:
            logger.warning(f"Feature Toggle routes not available: {e}")
        
        # Register AI Parent Assistant routes
        try:
            from app.routes.ai_assistant_routes import ai_assistant_bp
            app.register_blueprint(ai_assistant_bp, url_prefix="/api/ai-assistant")
            logger.info("✓ AI Parent Assistant routes registered")
        except Exception as e:
            logger.warning(f"AI Parent Assistant routes not available: {e}")
        
        # Register Smart Insights Dashboard routes
        try:
            from app.routes.insights_routes import insights_bp
            app.register_blueprint(insights_bp, url_prefix="/api/insights")
            logger.info("✓ Smart Insights routes registered")
        except Exception as e:
            logger.warning(f"Smart Insights routes not available: {e}")
        
        # Register Razorpay Webhook routes
        try:
            from app.routes.webhook_routes import webhook_bp
            app.register_blueprint(webhook_bp)
            logger.info("✓ Razorpay webhook routes registered")
        except Exception as e:
            logger.warning(f"Razorpay webhook routes not available: {e}")
        
        # Serve frontend static files
        from flask import send_from_directory
        import os
        
        frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend')
        
        @app.route('/')
        def index():
            return jsonify({
                "status": "online",
                "message": "School Management System API is running. Access the UI at /admin/dashboard.html"
            }), 200
        
        @app.route('/admin/<path:path>')
        def serve_admin(path):
            try:
                return send_from_directory(os.path.join(frontend_dir, 'admin'), path)
            except:
                return jsonify({"error": "File not found"}), 404
        
        @app.route('/auth/<path:path>')
        def serve_auth(path):
            try:
                return send_from_directory(os.path.join(frontend_dir, 'auth'), path)
            except:
                return jsonify({"error": "File not found"}), 404
        
        @app.route('/assets/<path:path>')
        def serve_assets(path):
            try:
                return send_from_directory(os.path.join(frontend_dir, 'assets'), path)
            except:
                return jsonify({"error": "File not found"}), 404
        
        logger.info("Application initialized successfully")
    
    return app