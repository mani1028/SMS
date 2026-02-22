from flask import Blueprint, request
from flask_jwt_extended import create_access_token
from app.services.auth_service import AuthService
from app.core.response import success_response, error_response

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new school"""
    try:
        data = request.get_json()
        
        # Validate input
        required_fields = ['school_name', 'school_email', 'admin_name', 'admin_email', 'admin_password']
        if not all(field in data for field in required_fields):
            return error_response("Missing required fields", 400)
        
        result = AuthService.register_school(
            school_name=data['school_name'],
            school_email=data['school_email'],
            admin_name=data['admin_name'],
            admin_email=data['admin_email'],
            admin_password=data['admin_password']
        )
        
        if result['success']:
            return success_response(result['message'], result, 201)
        else:
            return error_response(result['error'], 400)
    
    except Exception as e:
        return error_response(f"Registration failed: {str(e)}", 500)


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('email') or not data.get('password') or not data.get('school_id'):
            return error_response("Missing email, password, or school_id", 400)
        
        result = AuthService.login(
            email=data['email'],
            password=data['password'],
            school_id=data['school_id']
        )
        
        if result['success']:
            # Create JWT token
            access_token = create_access_token(identity=result['user_id'])
            
            response_data = result['user']
            response_data['token'] = access_token
            
            return success_response(result['message'], response_data)
        else:
            return error_response(result['error'], 401)
    
    except Exception as e:
        return error_response(f"Login failed: {str(e)}", 500)
