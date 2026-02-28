from flask import Blueprint, request
from flask_jwt_extended import create_access_token
from app.services.auth_service import AuthService
from app.core.response import success_response, error_response
from app.core.auth import token_required, permission_required
from app.core.validators import validate_schema, SCHOOL_REGISTER_SCHEMA, LOGIN_SCHEMA, ValidationError, InputValidator
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new school and admin user"""
    try:
        data = request.get_json()
        
        # Validate input against schema
        validate_schema(data, SCHOOL_REGISTER_SCHEMA)
        
        # Sanitize inputs
        school_name = InputValidator.sanitize_string(data.get('school_name'))
        school_email = InputValidator.sanitize_string(data.get('school_email')).lower()
        admin_name = InputValidator.sanitize_string(data.get('admin_name'))
        admin_email = InputValidator.sanitize_string(data.get('admin_email')).lower()
        admin_password = data.get('admin_password')
        
        # Additional validation
        InputValidator.validate_email(school_email)
        InputValidator.validate_email(admin_email)
        InputValidator.validate_string(admin_password, 'admin_password', min_length=8)
        
        result = AuthService.register_school(
            school_name=school_name,
            school_email=school_email,
            admin_name=admin_name,
            admin_email=admin_email,
            admin_password=admin_password
        )
        
        if result['success']:
            return success_response(result['message'], result, 201)
        else:
            return error_response(result['error'], 400)
    
    except ValidationError as e:
        logger.warning(f"Validation error in register: {str(e)}")
        return error_response(str(e), 400)
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return error_response(f"Registration failed: {str(e)}", 500)


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and return JWT token"""
    try:
        data = request.get_json()
        
        # Validate input against schema
        validate_schema(data, LOGIN_SCHEMA)
        
        # Sanitize email
        email = InputValidator.sanitize_string(data.get('email')).lower()
        password = data.get('password')
        school_id = InputValidator.validate_integer(data.get('school_id'), 'school_id', min_val=1)
        
        # Additional validation
        InputValidator.validate_email(email)
        
        result = AuthService.login(
            email=email,
            password=password,
            school_id=school_id
        )
        
        if result['success']:
            # Create JWT token
            access_token = create_access_token(identity=str(result['user_id']))
            
            response_data = result['user']
            response_data['token'] = access_token
            
            return success_response(result['message'], response_data)
        else:
            return error_response(result['error'], 401)
    
    except ValidationError as e:
        logger.warning(f"Validation error in login: {str(e)}")
        return error_response(str(e), 400)
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return error_response(f"Login failed: {str(e)}", 500)


@auth_bp.route('/verify', methods=['GET'])
@token_required
def verify_token(current_user):
    """Verify JWT token and return user info (no-op on success)"""
    return success_response(
        "Token verified",
        {
            "user_id": current_user.id,
            "email": current_user.email,
            "school_id": current_user.school_id,
            "role": current_user.role.to_dict() if current_user.role else None
        }
    )
