from flask import Blueprint, request
from app.services.student_service import StudentService
from app.core.response import success_response, error_response
from app.core.auth import token_required, role_required

student_bp = Blueprint('student', __name__)


@student_bp.route('/students', methods=['GET'])
@token_required
def get_students(current_user):
    """Get all students for a school"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        result = StudentService.get_students(
            school_id=current_user.school_id,
            page=page,
            limit=limit
        )
        
        if result['success']:
            return success_response(
                "Students retrieved successfully",
                {
                    "students": result['students'],
                    "total": result['total'],
                    "pages": result['pages'],
                    "current_page": result['current_page']
                }
            )
        else:
            return error_response(result['error'], 400)
    
    except Exception as e:
        return error_response(f"Error retrieving students: {str(e)}", 500)


@student_bp.route('/students/<int:student_id>', methods=['GET'])
@token_required
def get_student(current_user, student_id):
    """Get a specific student"""
    try:
        result = StudentService.get_student(
            student_id=student_id,
            school_id=current_user.school_id
        )
        
        if result['success']:
            return success_response("Student retrieved successfully", result['student'])
        else:
            return error_response(result['error'], result.get('status_code', 400))
    
    except Exception as e:
        return error_response(f"Error retrieving student: {str(e)}", 500)


@student_bp.route('/students', methods=['POST'])
@token_required
@role_required('Admin')
def create_student(current_user):
    """Create a new student"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('name') or not data.get('admission_no') or not data.get('class_name'):
            return error_response("Missing required fields", 400)
        
        result = StudentService.create_student(
            school_id=current_user.school_id,
            name=data['name'],
            admission_no=data['admission_no'],
            class_name=data['class_name'],
            email=data.get('email'),
            phone=data.get('phone')
        )
        
        if result['success']:
            return success_response(result['message'], result['student'], 201)
        else:
            return error_response(result['error'], 400)
    
    except Exception as e:
        return error_response(f"Error creating student: {str(e)}", 500)


@student_bp.route('/students/<int:student_id>', methods=['PUT'])
@token_required
@role_required('Admin')
def update_student(current_user, student_id):
    """Update a student"""
    try:
        data = request.get_json()
        
        result = StudentService.update_student(
            student_id=student_id,
            school_id=current_user.school_id,
            **data
        )
        
        if result['success']:
            return success_response(result['message'], result['student'])
        else:
            return error_response(result['error'], result.get('status_code', 400))
    
    except Exception as e:
        return error_response(f"Error updating student: {str(e)}", 500)


@student_bp.route('/students/<int:student_id>', methods=['DELETE'])
@token_required
@role_required('Admin')
def delete_student(current_user, student_id):
    """Delete a student"""
    try:
        result = StudentService.delete_student(
            student_id=student_id,
            school_id=current_user.school_id
        )
        
        if result['success']:
            return success_response(result['message'], {})
        else:
            return error_response(result['error'], result.get('status_code', 400))
    
    except Exception as e:
        return error_response(f"Error deleting student: {str(e)}", 500)
