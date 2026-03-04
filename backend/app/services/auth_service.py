from app.models.user import User
from app.models.school import School
from app.models.role import Role
from app.extensions import db
from app.core.rbac import initialize_rbac
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service"""
    
    @staticmethod
    def register_school(school_name, school_email, admin_name, admin_email, admin_password):
        """Register a new school with admin user"""
        try:
            # Check if school already exists
            existing_school = School.query.filter_by(email=school_email).first()
            if existing_school:
                return {"success": False, "error": "School already registered"}
            
            # Create school
            school = School(name=school_name, email=school_email)
            db.session.add(school)
            db.session.flush()
            
            # Initialize RBAC
            initialize_rbac(school.id)
            
            # Create admin user
            admin_role = Role.query.filter_by(school_id=school.id, name="Admin").first()
            admin_user = User(
                school_id=school.id,
                name=admin_name,
                email=admin_email,
                role_id=admin_role.id if admin_role else None
            )
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            
            db.session.commit()
            
            logger.info(f"School registered: {school_name}")
            return {
                "success": True,
                "school_id": school.id,
                "message": "School registered successfully"
            }
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def login(email, password, school_id):
        """Authenticate user"""
        try:
            user = User.query.filter_by(
                email=email,
                school_id=school_id,
                is_active=True
            ).first()
            
            if not user or not user.check_password(password):
                return {"success": False, "error": "Invalid credentials"}
            
            logger.info(f"User logged in: {email}")
            return {
                "success": True,
                "user_id": user.id,
                "user": user.to_dict(),
                "message": "Login successful"
            }
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def super_admin_login(email, password):
        """Super admin authentication (not school-scoped)"""
        try:
            user = User.query.filter_by(
                email=email,
                is_super_admin=True,
                is_active=True
            ).first()
            
            if not user or not user.check_password(password):
                return {"success": False, "error": "Invalid super admin credentials"}
            
            logger.info(f"Super admin logged in: {email}")
            return {
                "success": True,
                "user_id": user.id,
                "user": user.to_dict(),
                "message": "Super admin login successful"
            }
        except Exception as e:
            logger.error(f"Super admin login error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def verify_user(user_id, school_id):
        """Verify user belongs to school"""
        user = User.query.filter_by(id=user_id, school_id=school_id).first()
        return user is not None
