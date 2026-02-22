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
            current_user = User.query.get(user_id)
            
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
