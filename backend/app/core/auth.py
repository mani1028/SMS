from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from functools import wraps
from app.models.user import User
from app.core.response import error_response
import logging

logger = logging.getLogger(__name__)


def token_required(f):
    """Decorator to verify JWT token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()

            # JWT identity is stored as a string
            current_user = User.query.filter_by(id=int(user_id)).first()
            
            if not current_user:
                return error_response("User not found", 401)
            
            return f(current_user, *args, **kwargs)
        except Exception as e:
            logger.error(f"Auth error: {str(e)}")
            return error_response("Unauthorized", 401)
    
    return decorated_function


def role_required(required_role):
    """Decorator to check user role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(current_user, *args, **kwargs):
            if not current_user.role or current_user.role.name != required_role:
                return error_response("Insufficient permissions", 403)
            
            return f(current_user, *args, **kwargs)
        
        return decorated_function
    
    return decorator


def permission_required(*required_permissions):
    """
    Decorator to check if user has required permission(s).
    Can accept single permission or multiple permissions (OR logic).
    
    Usage:
        @permission_required('view_students')
        @permission_required('view_students', 'edit_students')  # User needs either permission
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(current_user, *args, **kwargs):
            # Check if user has a role
            if not current_user.role:
                logger.warning(f"User {current_user.id} has no role")
                return error_response("User has no role assigned", 403)
            
            # Get user's permissions
            user_permissions = {p.name for p in current_user.role.permissions}
            required_perms = set(required_permissions)
            
            # Check if user has at least one of the required permissions
            if not user_permissions.intersection(required_perms):
                logger.warning(
                    f"User {current_user.id} missing permissions. "
                    f"Required: {required_perms}, Has: {user_permissions}"
                )
                return error_response("Insufficient permissions", 403)
            
            return f(current_user, *args, **kwargs)
        
        return decorated_function
    
    return decorator