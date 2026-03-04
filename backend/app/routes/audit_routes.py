"""
Audit Log Routes
Track who edited marks, deleted records, changed fees, etc.
"""
from flask import Blueprint, request
from app.core.auth import token_required, permission_required
from app.core.response import success_response, error_response
from app.core.middleware import admin_required
from app.services.audit_service import AuditService
import logging

logger = logging.getLogger(__name__)

audit_bp = Blueprint('audit', __name__, url_prefix='/audit')


@audit_bp.route('/logs', methods=['GET'])
@token_required
@permission_required('view_audit_trail', 'view_audit_logs')
def get_audit_logs(current_user):
    """Get audit logs with filters"""
    try:
        from datetime import datetime

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        entity_type = request.args.get('entity_type')
        action = request.args.get('action')
        user_id = request.args.get('user_id', type=int)
        entity_id = request.args.get('entity_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)

        result = AuditService.get_logs(
            school_id=current_user.school_id,
            page=page, per_page=per_page,
            entity_type=entity_type, action=action,
            user_id=user_id, start_date=start_date,
            end_date=end_date, entity_id=entity_id
        )

        if result['success']:
            return success_response("Audit logs retrieved", result)
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Audit logs route error: {str(e)}")
        return error_response(str(e), 500)


@audit_bp.route('/entity/<string:entity_type>/<int:entity_id>', methods=['GET'])
@token_required
@permission_required('view_entity_history', 'view_audit_trail')
def get_entity_history(current_user, entity_type, entity_id):
    """Get complete change history for a specific entity"""
    try:
        result = AuditService.get_entity_history(
            current_user.school_id, entity_type, entity_id
        )
        if result['success']:
            return success_response("Entity history retrieved", result)
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Entity history route error: {str(e)}")
        return error_response(str(e), 500)


@audit_bp.route('/user/<int:user_id>/activity', methods=['GET'])
@token_required
@permission_required('view_user_activity', 'view_audit_trail')
def get_user_activity(current_user, user_id):
    """Get all actions performed by a specific user"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)

        result = AuditService.get_user_activity(
            current_user.school_id, user_id, page, per_page
        )
        if result['success']:
            return success_response("User activity retrieved", result)
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"User activity route error: {str(e)}")
        return error_response(str(e), 500)


@audit_bp.route('/summary', methods=['GET'])
@token_required
@permission_required('view_audit_trail', 'view_audit_logs')
def get_audit_summary(current_user):
    """Get audit summary for dashboard"""
    try:
        days = request.args.get('days', 30, type=int)
        result = AuditService.get_audit_summary(current_user.school_id, days)
        if result['success']:
            return success_response("Audit summary", result['summary'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Audit summary route error: {str(e)}")
        return error_response(str(e), 500)
