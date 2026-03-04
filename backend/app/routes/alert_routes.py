"""
Alert Routes
Smart alert system with configurable rules, auto-triggers, and notification management
"""
from flask import Blueprint, request
from app.core.auth import token_required, permission_required
from app.core.response import success_response, error_response
from app.core.middleware import admin_required
from app.services.alert_service import AlertService
import logging

logger = logging.getLogger(__name__)

alert_bp = Blueprint('alerts', __name__, url_prefix='/alerts')


# ── Alert CRUD ──────────────────────────────────────────────

@alert_bp.route('', methods=['POST'])
@token_required
@permission_required('create_alert', 'manage_alerts')
def create_alert(current_user):
    """Create a manual alert"""
    try:
        data = request.get_json()
        result = AlertService.create_alert(
            school_id=current_user.school_id,
            alert_type=data.get('alert_type'),
            title=data.get('title'),
            message=data.get('message'),
            severity=data.get('severity', 'info'),
            target_user_id=data.get('target_user_id'),
            target_role=data.get('target_role'),
            target_class_id=data.get('target_class_id'),
            entity_type=data.get('entity_type'),
            entity_id=data.get('entity_id'),
            channels=data.get('channels'),
            expires_at=data.get('expires_at')
        )
        if result['success']:
            return success_response("Alert created", result['data'], 201)
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Create alert error: {str(e)}")
        return error_response(str(e), 500)


@alert_bp.route('', methods=['GET'])
@token_required
@permission_required('view_alerts')
def get_alerts(current_user):
    """Get alerts for current user"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        severity = request.args.get('severity')

        result = AlertService.get_alerts(
            school_id=current_user.school_id,
            user_id=current_user.id,
            page=page, per_page=per_page,
            unread_only=unread_only,
            severity=severity
        )
        if result['success']:
            return success_response("Alerts retrieved", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Get alerts error: {str(e)}")
        return error_response(str(e), 500)


@alert_bp.route('/<int:alert_id>/read', methods=['PUT'])
@token_required
@permission_required('view_alerts')
def mark_alert_read(current_user, alert_id):
    """Mark a single alert as read"""
    try:
        result = AlertService.mark_read(
            current_user.school_id, alert_id, current_user.id
        )
        if result['success']:
            return success_response("Alert marked as read")
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Mark alert read error: {str(e)}")
        return error_response(str(e), 500)


@alert_bp.route('/read-all', methods=['PUT'])
@token_required
@permission_required('view_alerts')
def mark_all_read(current_user):
    """Mark all alerts as read"""
    try:
        result = AlertService.mark_all_read(
            current_user.school_id, current_user.id
        )
        if result['success']:
            return success_response(result['message'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Mark all read error: {str(e)}")
        return error_response(str(e), 500)


@alert_bp.route('/<int:alert_id>/dismiss', methods=['PUT'])
@token_required
@permission_required('view_alerts')
def dismiss_alert(current_user, alert_id):
    """Dismiss an alert"""
    try:
        result = AlertService.dismiss_alert(
            current_user.school_id, alert_id, current_user.id
        )
        if result['success']:
            return success_response("Alert dismissed")
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Dismiss alert error: {str(e)}")
        return error_response(str(e), 500)


# ── Alert Rules ─────────────────────────────────────────────

@alert_bp.route('/rules', methods=['POST'])
@token_required
@permission_required('manage_alerts')
def create_rule(current_user):
    """Create an alert automation rule"""
    try:
        data = request.get_json()
        result = AlertService.create_alert_rule(
            school_id=current_user.school_id,
            name=data.get('name'),
            alert_type=data.get('alert_type'),
            conditions=data.get('conditions', {}),
            severity=data.get('severity', 'warning'),
            message_template=data.get('message_template'),
            channels=data.get('channels', ['in_app']),
            frequency=data.get('frequency', 'daily'),
            target_role=data.get('target_role')
        )
        if result['success']:
            return success_response("Alert rule created", result['data'], 201)
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Create rule error: {str(e)}")
        return error_response(str(e), 500)


@alert_bp.route('/rules', methods=['GET'])
@token_required
@permission_required('manage_alerts', 'view_alerts')
def get_rules(current_user):
    """Get all alert rules"""
    try:
        result = AlertService.get_alert_rules(current_user.school_id)
        if result['success']:
            return success_response("Alert rules", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Get rules error: {str(e)}")
        return error_response(str(e), 500)


@alert_bp.route('/rules/<int:rule_id>/toggle', methods=['PUT'])
@token_required
@permission_required('manage_alerts')
def toggle_rule(current_user, rule_id):
    """Enable/disable an alert rule"""
    try:
        result = AlertService.toggle_rule(current_user.school_id, rule_id)
        if result['success']:
            return success_response(result['message'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Toggle rule error: {str(e)}")
        return error_response(str(e), 500)


# ── Auto Alert Triggers ────────────────────────────────────

@alert_bp.route('/trigger/low-attendance', methods=['POST'])
@token_required
@permission_required('manage_alerts')
def trigger_attendance_alerts(current_user):
    """Trigger low-attendance alerts based on threshold"""
    try:
        data = request.get_json() or {}
        threshold = data.get('threshold', 75)
        result = AlertService.generate_low_attendance_alerts(
            current_user.school_id, threshold
        )
        if result['success']:
            return success_response(result['message'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Attendance alert trigger error: {str(e)}")
        return error_response(str(e), 500)


@alert_bp.route('/trigger/fee-overdue', methods=['POST'])
@token_required
@permission_required('manage_alerts')
def trigger_fee_overdue_alerts(current_user):
    """Trigger fee overdue alerts"""
    try:
        result = AlertService.generate_fee_overdue_alerts(current_user.school_id)
        if result['success']:
            return success_response(result['message'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Fee overdue alert trigger error: {str(e)}")
        return error_response(str(e), 500)


@alert_bp.route('/trigger/exam-reminders', methods=['POST'])
@token_required
@permission_required('manage_alerts')
def trigger_exam_reminders(current_user):
    """Trigger exam reminder alerts"""
    try:
        data = request.get_json() or {}
        days_before = data.get('days_before', 3)
        result = AlertService.generate_exam_reminders(
            current_user.school_id, days_before
        )
        if result['success']:
            return success_response(result['message'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Exam reminder trigger error: {str(e)}")
        return error_response(str(e), 500)


@alert_bp.route('/trigger/all', methods=['POST'])
@token_required
@permission_required('manage_alerts')
def trigger_all_auto_alerts(current_user):
    """Run all automatic alert generators"""
    try:
        result = AlertService.run_all_auto_alerts(current_user.school_id)
        if result['success']:
            return success_response("All auto alerts processed", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Run all auto alerts error: {str(e)}")
        return error_response(str(e), 500)
