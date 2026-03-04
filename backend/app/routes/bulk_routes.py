"""
Bulk Operations Routes
Bulk student upload, fee assignment, attendance marking, promotion
"""
from flask import Blueprint, request
from app.core.auth import token_required, permission_required
from app.core.response import success_response, error_response
from app.core.middleware import admin_required, limit_request_size
from app.services.bulk_service import BulkOperationsService
import logging

logger = logging.getLogger(__name__)

bulk_bp = Blueprint('bulk', __name__, url_prefix='/bulk')


@bulk_bp.route('/students/upload', methods=['POST'])
@token_required
@permission_required('bulk_upload_students')
@limit_request_size(2000)
def bulk_upload_students(current_user):
    """Upload students via CSV text"""
    try:
        data = request.get_json()
        csv_data = data.get('csv_data')
        update_existing = data.get('update_existing', False)

        if not csv_data:
            return error_response("csv_data is required", 400)

        result = BulkOperationsService.bulk_upload_students(
            school_id=current_user.school_id,
            csv_data=csv_data,
            update_existing=update_existing
        )
        if result['success']:
            return success_response(result['message'], result['data'])
        return error_response(result.get('error', 'Upload failed'), 400)
    except Exception as e:
        logger.error(f"Bulk upload route error: {str(e)}")
        return error_response(str(e), 500)


@bulk_bp.route('/students/template', methods=['GET'])
@token_required
@permission_required('bulk_upload_students', 'view_students')
def get_csv_template(current_user):
    """Get CSV template for student upload"""
    try:
        result = BulkOperationsService.get_student_csv_template()
        return success_response("CSV template", result['data'])
    except Exception as e:
        return error_response(str(e), 500)


@bulk_bp.route('/students/export', methods=['GET'])
@token_required
@permission_required('bulk_export_students', 'export_data')
def export_students(current_user):
    """Export students as CSV"""
    try:
        class_name = request.args.get('class_name')
        status = request.args.get('status')
        result = BulkOperationsService.export_students_csv(
            current_user.school_id, class_name=class_name, status=status
        )
        if result['success']:
            return success_response("Students exported", result['data'])
        return error_response(result.get('error', 'Export failed'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@bulk_bp.route('/fees/assign', methods=['POST'])
@token_required
@permission_required('bulk_assign_fees')
@limit_request_size(2000)
def bulk_assign_fees(current_user):
    """Assign fee installments in bulk"""
    try:
        data = request.get_json()
        result = BulkOperationsService.bulk_assign_fees(
            school_id=current_user.school_id,
            class_id=data.get('class_id'),
            section_id=data.get('section_id'),
            student_ids=data.get('student_ids'),
            fee_plan_id=data.get('fee_plan_id'),
            academic_year=data.get('academic_year'),
            installments_data=data.get('installments')
        )
        if result['success']:
            return success_response(result['message'], result['data'])
        return error_response(result.get('error', 'Assignment failed'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@bulk_bp.route('/attendance/mark', methods=['POST'])
@token_required
@permission_required('bulk_mark_attendance', 'mark_attendance')
@limit_request_size(2000)
def bulk_mark_attendance(current_user):
    """Mark attendance for multiple students at once"""
    try:
        data = request.get_json()
        result = BulkOperationsService.bulk_mark_attendance(
            school_id=current_user.school_id,
            marked_by_id=current_user.id,
            attendance_date=data.get('attendance_date'),
            records=data.get('records', []),
            section_id=data.get('section_id'),
            subject_id=data.get('subject_id')
        )
        if result['success']:
            return success_response(result['message'], result['data'])
        return error_response(result.get('error', 'Marking failed'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@bulk_bp.route('/promote', methods=['POST'])
@token_required
@permission_required('bulk_promote', 'promote_students')
def bulk_promote(current_user):
    """Promote students from one class to another in bulk"""
    try:
        data = request.get_json()
        result = BulkOperationsService.bulk_promote_students(
            school_id=current_user.school_id,
            from_class_name=data.get('from_class'),
            to_class_name=data.get('to_class'),
            academic_year=data.get('academic_year'),
            initiated_by_id=current_user.id,
            student_ids=data.get('student_ids')
        )
        if result['success']:
            return success_response(result['message'], result['data'])
        return error_response(result.get('error', 'Promotion failed'), 400)
    except Exception as e:
        return error_response(str(e), 500)
