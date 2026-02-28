from flask import Blueprint, request
import logging

from app.core.auth import token_required, permission_required
from app.core.response import success_response, error_response
from app.services.parent_service import ParentService

logger = logging.getLogger(__name__)

parent_bp = Blueprint('parent', __name__)


@parent_bp.route('/parents', methods=['POST'])
@token_required
@permission_required('create_parent', 'create_student')
def create_parent(current_user):
    """Create a parent and link students."""
    try:
        payload = request.get_json() or {}
        result = ParentService.create_parent(current_user.school_id, payload)

        if result.get('success'):
            return success_response(
                result.get('message'),
                result.get('parent'),
                201
            )
        return error_response(result.get('error'), 400)
    except Exception as exc:
        logger.error(f'Create parent route error: {str(exc)}')
        return error_response(f'Error creating parent: {str(exc)}', 500)


@parent_bp.route('/parents/<int:parent_id>', methods=['GET'])
@token_required
@permission_required('view_parent', 'view_students')
def get_parent_profile(current_user, parent_id):
    """Get parent profile with linked students."""
    try:
        result = ParentService.get_parent_profile(parent_id, current_user.school_id)

        if result.get('success'):
            return success_response('Parent profile retrieved successfully', result.get('profile'))
        return error_response(result.get('error'), result.get('status_code', 400))
    except Exception as exc:
        logger.error(f'Get parent profile route error: {str(exc)}')
        return error_response(f'Error retrieving parent profile: {str(exc)}', 500)


@parent_bp.route('/parents/<int:parent_id>', methods=['PUT'])
@token_required
@permission_required('edit_parent', 'edit_student')
def update_parent(current_user, parent_id):
    """Update parent details and emergency contacts."""
    try:
        payload = request.get_json() or {}
        result = ParentService.update_parent(parent_id, current_user.school_id, payload)

        if result.get('success'):
            return success_response(result.get('message'), result.get('parent'))
        return error_response(result.get('error'), result.get('status_code', 400))
    except Exception as exc:
        logger.error(f'Update parent route error: {str(exc)}')
        return error_response(f'Error updating parent: {str(exc)}', 500)


@parent_bp.route('/parents/<int:parent_id>/communication', methods=['GET'])
@token_required
@permission_required('view_parent', 'view_students')
def get_parent_communications(current_user, parent_id):
    """Get communication history for a parent."""
    try:
        result = ParentService.get_communication_history(parent_id, current_user.school_id)

        if result.get('success'):
            return success_response(
                'Communication history retrieved successfully',
                {'communications': result.get('communications', [])}
            )
        return error_response(result.get('error'), result.get('status_code', 400))
    except Exception as exc:
        logger.error(f'Get parent communication route error: {str(exc)}')
        return error_response(f'Error retrieving communication history: {str(exc)}', 500)


@parent_bp.route('/parents/<int:parent_id>/communication', methods=['POST'])
@token_required
@permission_required('edit_parent', 'edit_student')
def add_parent_communication(current_user, parent_id):
    """Create communication log entry for a parent."""
    try:
        payload = request.get_json() or {}
        result = ParentService.add_communication_log(
            parent_id=parent_id,
            school_id=current_user.school_id,
            sent_by=current_user.id,
            payload=payload,
        )

        if result.get('success'):
            return success_response(
                result.get('message'),
                result.get('communication'),
                201
            )
        return error_response(result.get('error'), result.get('status_code', 400))
    except Exception as exc:
        logger.error(f'Add parent communication route error: {str(exc)}')
        return error_response(f'Error logging communication: {str(exc)}', 500)
