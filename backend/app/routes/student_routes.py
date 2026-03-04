from flask import Blueprint, request
from app.services.student_service import StudentService
from app.services.activity_service import ActivityService
from app.models.activity import ActivityType
from app.core.response import success_response, error_response
from app.core.auth import token_required, permission_required
from app.core.validators import InputValidator, validate_schema, STUDENT_CREATE_SCHEMA, STUDENT_UPDATE_SCHEMA, ValidationError
import logging

logger = logging.getLogger(__name__)

student_bp = Blueprint('student', __name__)


@student_bp.route('/students', methods=['GET'])
@token_required
@permission_required('view_students')
def get_students(current_user):
    """Get all students for a school (with pagination)"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        # Validate pagination params
        if page < 1:
            page = 1
        if limit < 1 or limit > 500:
            limit = 50
        
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
                    "current_page": result['current_page'],
                    "limit": limit
                }
            )
        else:
            return error_response(result['error'], 400)
    
    except Exception as e:
        logger.error(f"Get students error: {str(e)}")
        return error_response(f"Error retrieving students: {str(e)}", 500)


@student_bp.route('/students/<int:student_id>', methods=['GET'])
@token_required
@permission_required('view_students')
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
        logger.error(f"Get student error: {str(e)}")
        return error_response(f"Error retrieving student: {str(e)}", 500)


@student_bp.route('/students', methods=['POST'])
@token_required
@permission_required('create_student')
def create_student(current_user):
    """Create a new student"""
    try:
        data = request.get_json()
        
        # Validate input against schema
        validate_schema(data, STUDENT_CREATE_SCHEMA)
        
        # Sanitize inputs
        name = InputValidator.sanitize_string(data.get('name'))
        admission_no = InputValidator.sanitize_string(data.get('admission_no', '')) or None
        class_name = InputValidator.sanitize_string(data.get('class_name'))
        
        # Additional validation
        if admission_no:
            InputValidator.validate_admission_no(admission_no)
        
        email = InputValidator.sanitize_string(data.get('email', '')) or None
        phone = InputValidator.sanitize_string(data.get('phone', '')) or None
        
        if email:
            InputValidator.validate_email(email)
        if phone:
            InputValidator.validate_phone(phone)
        
        # Prepare kwargs for additional fields
        kwargs = {
            'section': InputValidator.sanitize_string(data.get('section', '')) or None,
            'roll_no': InputValidator.sanitize_string(data.get('roll_no', '')) or None,
            'email': email,
            'phone': phone,
            'gender': InputValidator.sanitize_string(data.get('gender', '')) or None,
            'dob': data.get('dob'),
            'blood_group': InputValidator.sanitize_string(data.get('blood_group', '')) or None,
            'address': InputValidator.sanitize_string(data.get('address', '')) or None,
            'previous_school': InputValidator.sanitize_string(data.get('previous_school', '')) or None,
            'admission_date': data.get('admission_date'),
            'parent_name': InputValidator.sanitize_string(data.get('parent_name', '')) or None,
            'parent_phone': InputValidator.sanitize_string(data.get('parent_phone', '')) or None,
            'parent_email': InputValidator.sanitize_string(data.get('parent_email', '')) or None,
        }
        
        result = StudentService.create_student(
            school_id=current_user.school_id,
            name=name,
            admission_no=admission_no,
            class_name=class_name,
            **kwargs
        )
        
        if result['success']:
            # Log activity
            ActivityService.log_activity(
                school_id=current_user.school_id,
                user_id=current_user.id,
                activity_type=ActivityType.STUDENT_CREATED.value,
                description=f"Created student: {name}",
                entity_type='student',
                entity_id=result['student']['id']
            )
            return success_response(result['message'], result['student'], 201)
        else:
            return error_response(result['error'], 400)
    
    except ValidationError as e:
        logger.warning(f"Validation error in create_student: {str(e)}")
        return error_response(str(e), 400)
    except Exception as e:
        logger.error(f"Create student error: {str(e)}")
        return error_response(f"Error creating student: {str(e)}", 500)


@student_bp.route('/students/<int:student_id>', methods=['PUT'])
@token_required
@permission_required('edit_student')
def update_student(current_user, student_id):
    """Update a student"""
    try:
        data = request.get_json()
        
        # Validate input against schema
        validate_schema(data, STUDENT_UPDATE_SCHEMA)
        
        # Sanitize inputs
        update_data = {}
        for key in ['name', 'class_name', 'email', 'phone', 'is_active']:
            if key in data and data[key] is not None:
                if key in ['name', 'class_name', 'email', 'phone']:
                    update_data[key] = InputValidator.sanitize_string(data[key])
                elif key == 'is_active':
                    update_data[key] = InputValidator.validate_boolean(data[key], key)
        
        result = StudentService.update_student(
            student_id=student_id,
            school_id=current_user.school_id,
            **update_data
        )
        
        if result['success']:
            # Log activity
            ActivityService.log_activity(
                school_id=current_user.school_id,
                user_id=current_user.id,
                activity_type=ActivityType.STUDENT_UPDATED.value,
                description=f"Updated student: {result['student']['name']}",
                entity_type='student',
                entity_id=student_id
            )
            return success_response(result['message'], result['student'])
        else:
            return error_response(result['error'], result.get('status_code', 400))
    
    except ValidationError as e:
        logger.warning(f"Validation error in update_student: {str(e)}")
        return error_response(str(e), 400)
    except Exception as e:
        logger.error(f"Update student error: {str(e)}")
        return error_response(f"Error updating student: {str(e)}", 500)


@student_bp.route('/students/<int:student_id>', methods=['DELETE'])
@token_required
@permission_required('delete_student')
def delete_student(current_user, student_id):
    """Delete a student (soft delete)"""
    try:
        result = StudentService.delete_student(
            student_id=student_id,
            school_id=current_user.school_id
        )
        
        if result['success']:
            # Log activity
            ActivityService.log_activity(
                school_id=current_user.school_id,
                user_id=current_user.id,
                activity_type=ActivityType.STUDENT_DELETED.value,
                description=f"Deleted student with ID: {student_id}",
                entity_type='student',
                entity_id=student_id
            )
            return success_response(result['message'], {})
        else:
            return error_response(result['error'], result.get('status_code', 400))
    
    except Exception as e:
        logger.error(f"Delete student error: {str(e)}")
        return error_response(f"Error deleting student: {str(e)}", 500)


@student_bp.route('/students/<int:student_id>/profile', methods=['GET'])
@token_required
@permission_required('view_student_profile', 'view_students')
def get_student_profile(current_user, student_id):
    """Get comprehensive student profile with all relations"""
    try:
        result = StudentService.get_student_profile(
            student_id=student_id,
            school_id=current_user.school_id
        )
        
        if result['success']:
            return success_response("Profile retrieved successfully", result['profile'])
        else:
            return error_response(result['error'], result.get('status_code', 400))
    
    except Exception as e:
        logger.error(f"Get student profile error: {str(e)}")
        return error_response(f"Error retrieving profile: {str(e)}", 500)


@student_bp.route('/students/promote', methods=['POST'])
@token_required
@permission_required('edit_student')
def promote_students(current_user):
    """Bulk promote students to next class"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('student_ids') or not isinstance(data['student_ids'], list):
            return error_response("student_ids (array) is required", 400)
        
        if not data.get('new_class'):
            return error_response("new_class is required", 400)
        
        student_ids = data['student_ids']
        new_class = InputValidator.sanitize_string(data['new_class'])
        new_section = InputValidator.sanitize_string(data.get('new_section', '')) or None
        academic_year = InputValidator.sanitize_string(data.get('academic_year', '')) or None
        
        result = StudentService.promote_students(
            school_id=current_user.school_id,
            student_ids=student_ids,
            new_class=new_class,
            new_section=new_section,
            academic_year=academic_year
        )
        
        if result['success']:
            # Log activity
            ActivityService.log_activity(
                school_id=current_user.school_id,
                user_id=current_user.id,
                activity_type=ActivityType.STUDENT_UPDATED.value,
                description=f"Promoted {result['promoted_count']} students to {new_class}",
                entity_type='student',
                entity_id=None
            )
            return success_response(result['message'], {
                "promoted_count": result['promoted_count'],
                "failed_students": result['failed_students']
            })
        else:
            return error_response(result['error'], 400)
    
    except Exception as e:
        logger.error(f"Promote students error: {str(e)}")
        return error_response(f"Error promoting students: {str(e)}", 500)


@student_bp.route('/students/<int:student_id>/tc', methods=['GET', 'POST'])
@token_required
@permission_required('edit_student')
def generate_transfer_certificate(current_user, student_id):
    """Generate Transfer Certificate for a student"""
    try:
        data = request.get_json() if request.method == 'POST' else {}
        
        reason = InputValidator.sanitize_string(data.get('reason', ''))
        remarks = InputValidator.sanitize_string(data.get('remarks', ''))
        
        result = StudentService.generate_tc(
            student_id=student_id,
            school_id=current_user.school_id,
            reason=reason,
            remarks=remarks
        )
        
        if result['success']:
            # Log activity
            ActivityService.log_activity(
                school_id=current_user.school_id,
                user_id=current_user.id,
                activity_type=ActivityType.STUDENT_UPDATED.value,
                description=f"Generated TC for student ID: {student_id}",
                entity_type='student',
                entity_id=student_id
            )
            return success_response(result['message'], result['tc_data'])
        else:
            return error_response(result['error'], result.get('status_code', 400))
    
    except Exception as e:
        logger.error(f"Generate TC error: {str(e)}")
        return error_response(f"Error generating TC: {str(e)}", 500)


@student_bp.route('/students/<int:student_id>/status', methods=['PUT'])
@token_required
@permission_required('edit_student')
def change_student_status(current_user, student_id):
    """Change student status"""
    try:
        data = request.get_json()
        
        if not data.get('status'):
            return error_response("status is required", 400)
        
        new_status = InputValidator.sanitize_string(data['status'])
        
        result = StudentService.change_student_status(
            student_id=student_id,
            school_id=current_user.school_id,
            new_status=new_status
        )
        
        if result['success']:
            # Log activity
            ActivityService.log_activity(
                school_id=current_user.school_id,
                user_id=current_user.id,
                activity_type=ActivityType.STUDENT_UPDATED.value,
                description=f"Changed status to {new_status} for student ID: {student_id}",
                entity_type='student',
                entity_id=student_id
            )
            return success_response(result['message'], result['student'])
        else:
            return error_response(result['error'], result.get('status_code', 400))
    
    except Exception as e:
        logger.error(f"Change status error: {str(e)}")
        return error_response(f"Error changing status: {str(e)}", 500)


@student_bp.route('/students/<int:student_id>/documents', methods=['POST'])
@token_required
@permission_required('edit_student')
def upload_student_document(current_user, student_id):
    """Upload document metadata for a student"""
    try:
        data = request.get_json()
        
        # Validate required fields
        InputValidator.validate_required_fields(data, ['doc_type', 'doc_name', 'file_path'])
        
        doc_type = InputValidator.sanitize_string(data['doc_type'])
        doc_name = InputValidator.sanitize_string(data['doc_name'])
        file_path = InputValidator.sanitize_string(data['file_path'])
        
        result = StudentService.add_document(
            school_id=current_user.school_id,
            student_id=student_id,
            doc_type=doc_type,
            doc_name=doc_name,
            file_path=file_path,
            file_size=data.get('file_size'),
            mime_type=data.get('mime_type')
        )
        
        if result['success']:
            # Log activity
            ActivityService.log_activity(
                school_id=current_user.school_id,
                user_id=current_user.id,
                activity_type=ActivityType.STUDENT_UPDATED.value,
                description=f"Added document {doc_type} for student ID: {student_id}",
                entity_type='student',
                entity_id=student_id
            )
            return success_response(result['message'], result['document'], 201)
        else:
            return error_response(result['error'], result.get('status_code', 400))
    
    except ValidationError as e:
        return error_response(str(e), 400)
    except Exception as e:
        logger.error(f"Upload document error: {str(e)}")
        return error_response(f"Error uploading document: {str(e)}", 500)


@student_bp.route('/students/<int:student_id>/academic-history', methods=['POST'])
@token_required
@permission_required('edit_student')
def add_academic_history(current_user, student_id):
    """Add academic history record for a student"""
    try:
        data = request.get_json()
        
        # Validate required fields
        InputValidator.validate_required_fields(data, ['class_name', 'academic_year'])
        
        class_name = InputValidator.sanitize_string(data['class_name'])
        academic_year = InputValidator.sanitize_string(data['academic_year'])
        
        result = StudentService.add_academic_record(
            school_id=current_user.school_id,
            student_id=student_id,
            class_name=class_name,
            academic_year=academic_year,
            section=data.get('section'),
            roll_no=data.get('roll_no'),
            result_data=data.get('result_data'),
            attendance_percentage=data.get('attendance_percentage'),
            final_result=data.get('final_result'),
            remarks=data.get('remarks')
        )
        
        if result['success']:
            return success_response(result['message'], result['record'], 201)
        else:
            return error_response(result['error'], result.get('status_code', 400))
    
    except ValidationError as e:
        return error_response(str(e), 400)
    except Exception as e:
        logger.error(f"Add academic history error: {str(e)}")
        return error_response(f"Error adding academic history: {str(e)}", 500)
