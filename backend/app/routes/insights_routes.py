"""
Smart Insights Dashboard Routes
=================================
Analytics endpoints for fee trends, attendance patterns, academic performance,
enrollment metrics, revenue forecast, and executive summary.
"""
from flask import Blueprint, request
from app.core.auth import token_required, permission_required
from app.core.response import success_response, error_response
from app.core.middleware import admin_required
from app.services.smart_insights_service import SmartInsightsService
import logging

logger = logging.getLogger(__name__)

insights_bp = Blueprint('insights', __name__, url_prefix='/insights')


@insights_bp.route('/fee-trends', methods=['GET'])
@token_required
@permission_required('view_fee_analytics', 'view_analytics')
def fee_trends(current_user):
    """Get fee collection trends."""
    try:
        months = request.args.get('months', 6, type=int)
        period = request.args.get('period', 'monthly')
        result = SmartInsightsService.get_fee_trends(
            current_user.school_id, period=period, months=months
        )
        if result['success']:
            return success_response("Fee trends", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Fee trends route error: {e}")
        return error_response(str(e), 500)


@insights_bp.route('/attendance', methods=['GET'])
@token_required
@permission_required('view_attendance_analytics', 'view_analytics')
def attendance_insights(current_user):
    """Get attendance patterns and at-risk students."""
    try:
        days = request.args.get('days', 30, type=int)
        result = SmartInsightsService.get_attendance_insights(
            current_user.school_id, days=days
        )
        if result['success']:
            return success_response("Attendance insights", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Attendance insights route error: {e}")
        return error_response(str(e), 500)


@insights_bp.route('/performance', methods=['GET'])
@token_required
@permission_required('view_student_analytics', 'view_analytics')
def performance_analytics(current_user):
    """Get academic performance analytics."""
    try:
        exam_term_id = request.args.get('exam_term_id', type=int)
        result = SmartInsightsService.get_performance_analytics(
            current_user.school_id, exam_term_id=exam_term_id
        )
        if result['success']:
            return success_response("Performance analytics", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Performance analytics route error: {e}")
        return error_response(str(e), 500)


@insights_bp.route('/enrollment', methods=['GET'])
@token_required
@permission_required('view_analytics', 'view_dashboard')
def enrollment_metrics(current_user):
    """Get enrollment and growth metrics."""
    try:
        months = request.args.get('months', 12, type=int)
        result = SmartInsightsService.get_enrollment_metrics(
            current_user.school_id, months=months
        )
        if result['success']:
            return success_response("Enrollment metrics", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Enrollment metrics route error: {e}")
        return error_response(str(e), 500)


@insights_bp.route('/revenue-forecast', methods=['GET'])
@token_required
@permission_required('view_fee_analytics', 'view_financial_overview')
def revenue_forecast(current_user):
    """Get revenue forecast based on upcoming installments."""
    try:
        result = SmartInsightsService.get_revenue_forecast(current_user.school_id)
        if result['success']:
            return success_response("Revenue forecast", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Revenue forecast route error: {e}")
        return error_response(str(e), 500)


@insights_bp.route('/executive-summary', methods=['GET'])
@token_required
@admin_required
def executive_summary(current_user):
    """Get one-page executive summary (Admin/Principal only)."""
    try:
        result = SmartInsightsService.get_executive_summary(current_user.school_id)
        if result['success']:
            return success_response("Executive summary", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Executive summary route error: {e}")
        return error_response(str(e), 500)
