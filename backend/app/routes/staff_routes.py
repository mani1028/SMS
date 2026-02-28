from flask import Blueprint, request
import logging

from app.core.auth import token_required, permission_required
from app.core.response import success_response, error_response
from app.services.staff_service import StaffService

logger = logging.getLogger(__name__)

staff_bp = Blueprint('staff', __name__)


@staff_bp.route('/staff', methods=['POST'])
@token_required
@permission_required('create_staff', 'manage_users')
def create_staff(current_user):
    """Register new staff and assign RBAC role."""
    try:
        payload = request.get_json() or {}
        result = StaffService.create_staff(current_user.school_id, payload)

        if result.get('success'):
            return success_response(result.get('message'), result.get('staff'), 201)
        return error_response(result.get('error'), 400)
    except Exception as exc:
        logger.error(f'Create staff route error: {str(exc)}')
        return error_response(f'Error creating staff: {str(exc)}', 500)


@staff_bp.route('/staff/profile/<int:staff_id>', methods=['GET'])
@token_required
@permission_required('view_staff', 'manage_users')
def get_staff_profile(current_user, staff_id):
    """Detailed staff profile including salary and role."""
    try:
        result = StaffService.get_staff_profile(staff_id, current_user.school_id)

        if result.get('success'):
            return success_response('Staff profile retrieved successfully', result.get('profile'))
        return error_response(result.get('error'), result.get('status_code', 400))
    except Exception as exc:
        logger.error(f'Get staff profile route error: {str(exc)}')
        return error_response(f'Error retrieving staff profile: {str(exc)}', 500)


@staff_bp.route('/staff/attendance', methods=['POST'])
@token_required
@permission_required('manage_staff_attendance', 'edit_staff')
def record_staff_attendance(current_user):
    """Submit daily bulk attendance for staff."""
    try:
        payload = request.get_json() or {}
        attendance_date = payload.get('date')
        records = payload.get('records', [])

        result = StaffService.record_attendance(
            school_id=current_user.school_id,
            attendance_date=attendance_date,
            records=records,
        )

        if result.get('success'):
            return success_response(result.get('message'), {
                'attendance': result.get('attendance', [])
            })
        return error_response(result.get('error'), 400)
    except Exception as exc:
        logger.error(f'Record staff attendance route error: {str(exc)}')
        return error_response(f'Error recording attendance: {str(exc)}', 500)


@staff_bp.route('/staff/leaves', methods=['POST'])
@token_required
@permission_required('manage_staff_leaves', 'edit_staff')
def process_staff_leave(current_user):
    """Submit or process leave requests."""
    try:
        payload = request.get_json() or {}
        result = StaffService.process_leave(
            school_id=current_user.school_id,
            payload=payload,
            reviewer_user_id=current_user.id,
        )

        if result.get('success'):
            return success_response(result.get('message'), result.get('leave_request'))
        return error_response(result.get('error'), 400)
    except Exception as exc:
        logger.error(f'Process staff leave route error: {str(exc)}')
        return error_response(f'Error processing leave request: {str(exc)}', 500)


@staff_bp.route('/staff/id-card/<int:staff_id>', methods=['GET'])
@token_required
@permission_required('view_staff', 'manage_users')
def get_staff_id_card_data(current_user, staff_id):
    """Get all data needed for ID card generation."""
    try:
        result = StaffService.generate_id_card_data(staff_id, current_user.school_id)

        if result.get('success'):
            return success_response('ID card data retrieved successfully', result.get('id_card_data'))
        return error_response(result.get('error'), result.get('status_code', 400))
    except Exception as exc:
        logger.error(f'Get ID card data route error: {str(exc)}')
        return error_response(f'Error generating ID card data: {str(exc)}', 500)
