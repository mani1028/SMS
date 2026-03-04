"""
Academic Management Routes
Routes for managing classes, sections, subjects, teachers, and timetables
"""

from flask import Blueprint, request, current_app
from app.core.auth import token_required
from app.core.rbac import permission_required
from app.core.response import success_response, error_response
from app.core.validators import InputValidator, validate_schema, CLASS_CREATE_SCHEMA, SECTION_CREATE_SCHEMA, SUBJECT_CREATE_SCHEMA, TIMETABLE_SLOT_SCHEMA
from app.services.academics_service import AcademicsService
from app.services.settings_service import AuditService
from datetime import datetime

academic_bp = Blueprint('academics', __name__, url_prefix='/api/academics')

# ==================== CLASS ROUTES ====================

@academic_bp.route('/classes', methods=['POST'])
@token_required
@permission_required('create_class')
def create_class(current_user):
    """Create a new class"""
    try:
        data = request.get_json()
        validate_schema(data, CLASS_CREATE_SCHEMA)
        
        # Validate inputs
        if not InputValidator.validate_string(data['name'], 2, 50):
            return error_response("Invalid class name", 400)
        
        if not InputValidator.validate_integer(data['numeric_class'], 1, 12):
            return error_response("Invalid class number (1-12)", 400)
        
        result = AcademicsService.create_class(
            school_id=current_user.school_id,
            name=data['name'],
            numeric_class=data['numeric_class'],
            description=data.get('description', '')
        )
        
        if result['success']:
            # Audit log
            AuditService.log_action(
                school_id=current_user.school_id,
                user_id=current_user.id,
                action='CREATE_CLASS',
                entity_type='Class',
                entity_id=result['class'].id,
                new_values={'name': data['name'], 'numeric_class': data['numeric_class']}
            )
            return success_response("Class created successfully", result['class'].to_dict(), 201)
        
        return error_response(result.get('error', 'Failed to create class'), 400)
    
    except Exception as e:
        current_app.logger.error(f"Error creating class: {str(e)}")
        return error_response("Internal server error", 500)


@academic_bp.route('/classes', methods=['GET'])
@token_required
@permission_required('view_class')
def get_classes(current_user):
    """Get all classes for the school"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        numeric_class = request.args.get('numeric_class', None, type=int)
        
        result = AcademicsService.get_classes(
            school_id=current_user.school_id,
            page=page,
            limit=limit,
            numeric_class=numeric_class
        )
        
        return success_response(
            "Classes retrieved",
            {
                'classes': [c.to_dict() for c in result['classes']],
                'total': result['total'],
                'pages': result['pages']
            }
        )
    
    except Exception as e:
        current_app.logger.error(f"Error fetching classes: {str(e)}")
        return error_response("Internal server error", 500)


@academic_bp.route('/classes/<int:class_id>', methods=['GET'])
@token_required
@permission_required('view_class')
def get_class(current_user, class_id):
    """Get specific class details"""
    try:
        from app.models.academics import Class
        cls = Class.query.filter_by(id=class_id, school_id=current_user.school_id).first()
        
        if not cls:
            return error_response("Class not found", 404)
        
        return success_response("Class retrieved", cls.to_dict())
    
    except Exception as e:
        current_app.logger.error(f"Error fetching class: {str(e)}")
        return error_response("Internal server error", 500)


@academic_bp.route('/classes/<int:class_id>', methods=['PUT'])
@token_required
@permission_required('edit_class')
def update_class(current_user, class_id):
    """Update class details"""
    try:
        from app.models.academics import Class
        from app import db
        
        cls = Class.query.filter_by(id=class_id, school_id=current_user.school_id).first()
        if not cls:
            return error_response("Class not found", 404)
        
        data = request.get_json()
        old_values = {'name': cls.name, 'description': cls.description}
        
        if 'name' in data:
            if not InputValidator.validate_string(data['name'], 2, 50):
                return error_response("Invalid class name", 400)
            cls.name = data['name']
        
        if 'description' in data:
            cls.description = data.get('description', '')
        
        db.session.commit()
        
        # Audit log
        AuditService.log_action(
            school_id=current_user.school_id,
            user_id=current_user.id,
            action='UPDATE_CLASS',
            entity_type='Class',
            entity_id=class_id,
            old_values=old_values,
            new_values=data
        )
        
        return success_response("Class updated successfully", cls.to_dict())
    
    except Exception as e:
        current_app.logger.error(f"Error updating class: {str(e)}")
        return error_response("Internal server error", 500)


# ==================== SECTION ROUTES ====================

@academic_bp.route('/sections', methods=['POST'])
@token_required
@permission_required('create_section')
def create_section(current_user):
    """Create a new section"""
    try:
        data = request.get_json()
        validate_schema(data, SECTION_CREATE_SCHEMA)
        
        if not InputValidator.validate_string(data['name'], 1, 10):
            return error_response("Invalid section name", 400)
        
        if not InputValidator.validate_integer(data.get('capacity', 45), 1, 100):
            return error_response("Invalid capacity", 400)
        
        result = AcademicsService.create_section(
            school_id=current_user.school_id,
            class_id=data['class_id'],
            name=data['name'],
            capacity=data.get('capacity', 45)
        )
        
        if result['success']:
            AuditService.log_action(
                school_id=current_user.school_id,
                user_id=current_user.id,
                action='CREATE_SECTION',
                entity_type='Section',
                entity_id=result['section'].id,
                new_values=data
            )
            return success_response("Section created successfully", result['section'].to_dict(), 201)
        
        return error_response(result.get('error', 'Failed to create section'), 400)
    
    except Exception as e:
        current_app.logger.error(f"Error creating section: {str(e)}")
        return error_response("Internal server error", 500)


@academic_bp.route('/classes/<int:class_id>/sections', methods=['GET'])
@token_required
@permission_required('view_section')
def get_sections_by_class(current_user, class_id):
    """Get sections for a specific class"""
    try:
        result = AcademicsService.get_sections_by_class(
            school_id=current_user.school_id,
            class_id=class_id
        )
        
        if result['success']:
            return success_response(
                "Sections retrieved",
                {'sections': [s.to_dict() for s in result['sections']]}
            )
        
        return error_response(result.get('error', 'Failed to fetch sections'), 400)
    
    except Exception as e:
        current_app.logger.error(f"Error fetching sections: {str(e)}")
        return error_response("Internal server error", 500)


# ==================== SUBJECT ROUTES ====================

@academic_bp.route('/subjects', methods=['POST'])
@token_required
@permission_required('create_subject')
def create_subject(current_user):
    """Create a new subject"""
    try:
        data = request.get_json()
        validate_schema(data, SUBJECT_CREATE_SCHEMA)
        
        if not InputValidator.validate_string(data['name'], 2, 50):
            return error_response("Invalid subject name", 400)
        
        if not InputValidator.validate_string(data.get('code', ''), 1, 10):
            return error_response("Invalid subject code", 400)
        
        result = AcademicsService.create_subject(
            school_id=current_user.school_id,
            name=data['name'],
            code=data.get('code', ''),
            description=data.get('description', '')
        )
        
        if result['success']:
            AuditService.log_action(
                school_id=current_user.school_id,
                user_id=current_user.id,
                action='CREATE_SUBJECT',
                entity_type='Subject',
                entity_id=result['subject'].id,
                new_values=data
            )
            return success_response("Subject created successfully", result['subject'].to_dict(), 201)
        
        return error_response(result.get('error', 'Failed to create subject'), 400)
    
    except Exception as e:
        current_app.logger.error(f"Error creating subject: {str(e)}")
        return error_response("Internal server error", 500)


@academic_bp.route('/subjects', methods=['GET'])
@token_required
@permission_required('view_subject')
def get_subjects(current_user):
    """Get all subjects for the school"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        result = AcademicsService.get_subjects(
            school_id=current_user.school_id,
            page=page,
            limit=limit
        )
        
        return success_response(
            "Subjects retrieved",
            {
                'subjects': [s.to_dict() for s in result['subjects']],
                'total': result['total'],
                'pages': result['pages']
            }
        )
    
    except Exception as e:
        current_app.logger.error(f"Error fetching subjects: {str(e)}")
        return error_response("Internal server error", 500)


# ==================== TEACHER ASSIGNMENT ROUTES ====================

@academic_bp.route('/teacher-assignments', methods=['POST'])
@token_required
@permission_required('assign_teacher')
def assign_teacher(current_user):
    """Assign teacher to class-section-subject"""
    try:
        data = request.get_json()
        
        result = AcademicsService.assign_teacher(
            school_id=current_user.school_id,
            class_id=data['class_id'],
            section_id=data['section_id'],
            teacher_id=data['teacher_id'],
            subject_id=data['subject_id']
        )
        
        if result['success']:
            AuditService.log_action(
                school_id=current_user.school_id,
                user_id=current_user.id,
                action='ASSIGN_TEACHER',
                entity_type='ClassTeacherAssignment',
                entity_id=result['assignment'].id,
                new_values=data
            )
            return success_response("Teacher assigned successfully", result['assignment'].to_dict(), 201)
        
        return error_response(result.get('error', 'Failed to assign teacher'), 400)
    
    except Exception as e:
        current_app.logger.error(f"Error assigning teacher: {str(e)}")
        return error_response("Internal server error", 500)


@academic_bp.route('/class-sections/<int:class_id>/<int:section_id>/teachers', methods=['GET'])
@token_required
@permission_required('view_teacher_assignment')
def get_section_teachers(current_user, class_id, section_id):
    """Get all teacher assignments for a section"""
    try:
        from app.models.academics import ClassTeacherAssignment
        
        assignments = ClassTeacherAssignment.query.filter_by(
            school_id=current_user.school_id,
            class_id=class_id,
            section_id=section_id
        ).all()
        
        return success_response(
            "Assignments retrieved",
            {'assignments': [a.to_dict() for a in assignments]}
        )
    
    except Exception as e:
        current_app.logger.error(f"Error fetching assignments: {str(e)}")
        return error_response("Internal server error", 500)


# ==================== TIMETABLE ROUTES ====================

@academic_bp.route('/timetables', methods=['POST'])
@token_required
@permission_required('create_timetable')
def create_timetable_slot(current_user):
    """Create a timetable slot"""
    try:
        data = request.get_json()
        validate_schema(data, TIMETABLE_SLOT_SCHEMA)
        
        # Validate time format (HH:MM)
        try:
            datetime.strptime(data['start_time'], '%H:%M')
            datetime.strptime(data['end_time'], '%H:%M')
        except ValueError:
            return error_response("Invalid time format. Use HH:MM", 400)
        
        # Check for conflicts
        conflict = AcademicsService.check_timetable_conflict(
            school_id=current_user.school_id,
            teacher_id=data['teacher_id'],
            day_of_week=data['day_of_week'],
            start_time=data['start_time'],
            end_time=data['end_time']
        )
        
        if conflict:
            return error_response("Teacher has conflicting timetable slot", 409)
        
        result = AcademicsService.create_timetable_slot(
            school_id=current_user.school_id,
            class_id=data['class_id'],
            section_id=data['section_id'],
            teacher_id=data['teacher_id'],
            subject_id=data['subject_id'],
            day_of_week=data['day_of_week'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            room_number=data.get('room_number', '')
        )
        
        if result['success']:
            AuditService.log_action(
                school_id=current_user.school_id,
                user_id=current_user.id,
                action='CREATE_TIMETABLE',
                entity_type='TimetableSlot',
                entity_id=result['slot'].id,
                new_values=data
            )
            return success_response("Timetable slot created successfully", result['slot'].to_dict(), 201)
        
        return error_response(result.get('error', 'Failed to create timetable slot'), 400)
    
    except Exception as e:
        current_app.logger.error(f"Error creating timetable: {str(e)}")
        return error_response("Internal server error", 500)


@academic_bp.route('/timetables/section/<int:section_id>', methods=['GET'])
@token_required
@permission_required('view_timetable')
def get_section_timetable(current_user, section_id):
    """Get timetable for a section"""
    try:
        result = AcademicsService.get_timetable(
            school_id=current_user.school_id,
            section_id=section_id
        )
        
        if result['success']:
            return success_response(
                "Timetable retrieved",
                {'timetable': [t.to_dict() for t in result['timetable']]}
            )
        
        return error_response(result.get('error', 'Failed to fetch timetable'), 400)
    
    except Exception as e:
        current_app.logger.error(f"Error fetching timetable: {str(e)}")
        return error_response("Internal server error", 500)


@academic_bp.route('/timetables/teacher/<int:teacher_id>', methods=['GET'])
@token_required
@permission_required('view_timetable')
def get_teacher_timetable(current_user, teacher_id):
    """Get timetable for a teacher"""
    try:
        from app.models.academics import TimetableSlot
        
        slots = TimetableSlot.query.filter_by(
            school_id=current_user.school_id,
            teacher_id=teacher_id
        ).order_by(TimetableSlot.day_of_week, TimetableSlot.start_time).all()
        
        return success_response(
            "Teacher timetable retrieved",
            {'timetable': [s.to_dict() for s in slots]}
        )
    
    except Exception as e:
        current_app.logger.error(f"Error fetching teacher timetable: {str(e)}")
        return error_response("Internal server error", 500)


@academic_bp.route('/timetables/<int:slot_id>', methods=['DELETE'])
@token_required
@permission_required('delete_timetable')
def delete_timetable_slot(current_user, slot_id):
    """Delete a timetable slot"""
    try:
        from app.models.academics import TimetableSlot
        from app import db
        
        slot = TimetableSlot.query.filter_by(id=slot_id, school_id=current_user.school_id).first()
        if not slot:
            return error_response("Timetable slot not found", 404)
        
        old_values = {
            'day_of_week': slot.day_of_week,
            'start_time': slot.start_time,
            'end_time': slot.end_time
        }
        
        db.session.delete(slot)
        db.session.commit()
        
        AuditService.log_action(
            school_id=current_user.school_id,
            user_id=current_user.id,
            action='DELETE_TIMETABLE',
            entity_type='TimetableSlot',
            entity_id=slot_id,
            old_values=old_values
        )
        
        return success_response("Timetable slot deleted successfully")
    
    except Exception as e:
        current_app.logger.error(f"Error deleting timetable slot: {str(e)}")
        return error_response("Internal server error", 500)
