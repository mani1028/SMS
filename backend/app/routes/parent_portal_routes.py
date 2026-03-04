"""
Parent Portal Routes
Web/mobile friendly endpoints for parents to view student data
"""
from flask import Blueprint, request
from app.core.auth import token_required, permission_required
from app.core.response import success_response, error_response
from app.services.parent_portal_service import ParentPortalService
import logging

logger = logging.getLogger(__name__)

parent_portal_bp = Blueprint('parent_portal', __name__, url_prefix='/parent-portal')


@parent_portal_bp.route('/student/<int:student_id>/overview', methods=['GET'])
@token_required
@permission_required('view_child_overview', 'view_students')
def student_overview(current_user, student_id):
    """Get student overview dashboard for parent"""
    try:
        result = ParentPortalService.get_student_overview(
            current_user.school_id, student_id
        )
        if result['success']:
            return success_response("Student overview", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Parent portal overview error: {str(e)}")
        return error_response(str(e), 500)


@parent_portal_bp.route('/student/<int:student_id>/attendance', methods=['GET'])
@token_required
@permission_required('view_child_attendance', 'view_attendance')
def student_attendance(current_user, student_id):
    """Get student attendance details"""
    try:
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)

        result = ParentPortalService.get_attendance_view(
            current_user.school_id, student_id, month, year
        )
        if result['success']:
            return success_response("Attendance data", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Parent portal attendance error: {str(e)}")
        return error_response(str(e), 500)


@parent_portal_bp.route('/student/<int:student_id>/marks', methods=['GET'])
@token_required
@permission_required('view_child_marks', 'view_grades')
def student_marks(current_user, student_id):
    """Get student marks and grades"""
    try:
        exam_term_id = request.args.get('exam_term_id', type=int)

        result = ParentPortalService.get_marks_view(
            current_user.school_id, student_id, exam_term_id
        )
        if result['success']:
            return success_response("Marks data", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Parent portal marks error: {str(e)}")
        return error_response(str(e), 500)


@parent_portal_bp.route('/student/<int:student_id>/fees', methods=['GET'])
@token_required
@permission_required('view_child_fees', 'view_fees')
def student_fees(current_user, student_id):
    """Get student fee status and payment history"""
    try:
        result = ParentPortalService.get_fee_status(
            current_user.school_id, student_id
        )
        if result['success']:
            return success_response("Fee status", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Parent portal fees error: {str(e)}")
        return error_response(str(e), 500)


@parent_portal_bp.route('/student/<int:student_id>/homework', methods=['GET'])
@token_required
@permission_required('view_child_overview', 'view_homework')
def student_homework(current_user, student_id):
    """Get homework assignments for a student"""
    try:
        class_id = request.args.get('class_id', type=int)

        result = ParentPortalService.get_homework_view(
            current_user.school_id, student_id, class_id
        )
        if result['success']:
            return success_response("Homework data", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Parent portal homework error: {str(e)}")
        return error_response(str(e), 500)


@parent_portal_bp.route('/student/<int:student_id>/notifications', methods=['GET'])
@token_required
@permission_required('view_child_overview', 'view_notices')
def student_notifications(current_user, student_id):
    """Get notifications for a parent (notices, alerts, events)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        result = ParentPortalService.get_notifications(
            current_user.school_id, student_id, page, per_page
        )
        if result['success']:
            return success_response("Notifications", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Parent portal notifications error: {str(e)}")
        return error_response(str(e), 500)
