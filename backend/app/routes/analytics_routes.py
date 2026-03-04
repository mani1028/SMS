"""
Analytics Routes
Student performance, class analytics, admission funnel, attendance analytics
"""
from flask import Blueprint, request
from app.core.auth import token_required, permission_required
from app.core.decorators.requires_feature import requires_feature
from app.core.response import success_response, error_response
from app.services.analytics_service import AnalyticsService
import logging

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__)


# ==================== PLATFORM DASHBOARD ====================

@analytics_bp.route('/dashboard', methods=['GET'])
@token_required
def platform_dashboard(current_user):
    """Get platform-wide analytics for dashboard"""
    try:
        from app.models.school import School
        from app.models.billing import Subscription, Plan
        from app.models.user import User
        from app.models.student import Student
        from app.models.staff import Staff
        from app.models.billing import Billing
        
        # Get schools statistics - use subscription_status not status
        total_schools = School.query.count()
        active_schools = School.query.filter_by(subscription_status='active').count()
        
        # Count trial schools - look for 'trial' or count others
        trial_schools = 0
        try:
            trial_schools = School.query.filter_by(subscription_status='trial').count()
        except:
            trial_schools = 0
        
        # Get revenue data
        total_revenue = 0
        try:
            billings = Billing.query.filter_by(status='paid').all()
            for billing in billings:
                total_revenue += billing.amount or 0
        except:
            total_revenue = 0
        
        # Get users statistics
        total_users = User.query.count()
        try:
            students_count = Student.query.count()
        except:
            students_count = 0
        try:
            staff_count = Staff.query.count()
        except:
            staff_count = 0
        
        # Get payment failures
        try:
            failed_payments = Billing.query.filter_by(status='failed').count()
        except:
            failed_payments = 0
        
        # Get subscription distribution
        subscriptions = {}
        try:
            subs = Subscription.query.all()
            for sub in subs:
                plan = Plan.query.get(sub.plan_id)
                plan_name = plan.name if plan else 'Unknown'
                subscriptions[plan_name] = subscriptions.get(plan_name, 0) + 1
        except:
            subscriptions = {}
        
        dashboard_data = {
            'schools': {
                'total': total_schools,
                'active': active_schools,
                'trial': trial_schools
            },
            'revenue': {
                'total': total_revenue,
                'currency': 'INR'
            },
            'users': {
                'total': total_users,
                'students': students_count,
                'staff': staff_count
            },
            'payments': {
                'failed_count': failed_payments
            },
            'subscriptions': subscriptions
        }
        
        return success_response("Platform dashboard analytics", dashboard_data)
    except Exception as e:
        logger.error(f"Platform dashboard error: {str(e)}")
        return error_response(str(e), 500)


# ==================== STUDENT PERFORMANCE ====================

@analytics_bp.route('/student/<int:student_id>/performance', methods=['GET'])
@token_required
@permission_required('view_student_analytics', 'view_analytics')
@requires_feature('analytics')
def student_performance(current_user, student_id):
    """Get student performance analytics (subject trends, weak subjects, etc.)"""
    try:
        academic_year = request.args.get('academic_year')
        result = AnalyticsService.get_student_performance(
            current_user.school_id, student_id, academic_year
        )
        if result['success']:
            return success_response("Student performance analytics", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Student performance route error: {str(e)}")
        return error_response(str(e), 500)


@analytics_bp.route('/class/<int:class_id>/performance', methods=['GET'])
@token_required
@permission_required('view_student_analytics', 'view_analytics')
@requires_feature('analytics')
def class_performance(current_user, class_id):
    """Get class performance analytics (top students, averages, pass/fail)"""
    try:
        exam_term_id = request.args.get('exam_term_id', type=int)
        result = AnalyticsService.get_class_performance(
            current_user.school_id, class_id, exam_term_id
        )
        if result['success']:
            return success_response("Class performance analytics", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Class performance route error: {str(e)}")
        return error_response(str(e), 500)


@analytics_bp.route('/teacher/performance', methods=['GET'])
@token_required
@permission_required('view_analytics')
@requires_feature('analytics')
def teacher_performance(current_user):
    """Get teacher performance comparison based on student results"""
    try:
        teacher_id = request.args.get('teacher_id', type=int)
        result = AnalyticsService.get_teacher_performance(
            current_user.school_id, teacher_id
        )
        if result['success']:
            return success_response("Teacher performance analytics", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Teacher performance route error: {str(e)}")
        return error_response(str(e), 500)


# ==================== ADMISSION FUNNEL ====================

@analytics_bp.route('/admission-funnel', methods=['GET'])
@token_required
@permission_required('view_analytics', 'view_enquiries')
@requires_feature('analytics')
def admission_funnel(current_user):
    """Get admission funnel analytics (conversion %, source performance, monthly trends)"""
    try:
        from datetime import datetime
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)

        result = AnalyticsService.get_admission_funnel(
            current_user.school_id, start_date, end_date
        )
        if result['success']:
            return success_response("Admission funnel analytics", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Admission funnel route error: {str(e)}")
        return error_response(str(e), 500)


# ==================== ATTENDANCE ANALYTICS ====================

@analytics_bp.route('/attendance', methods=['GET'])
@token_required
@permission_required('view_attendance_analytics', 'view_analytics')
@requires_feature('analytics')
def attendance_analytics(current_user):
    """Get attendance analytics (trends, low attendance students)"""
    try:
        from datetime import datetime
        class_id = request.args.get('class_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if start_date:
            start_date = datetime.fromisoformat(start_date).date()
        if end_date:
            end_date = datetime.fromisoformat(end_date).date()

        result = AnalyticsService.get_attendance_analytics(
            current_user.school_id, class_id, start_date, end_date
        )
        if result['success']:
            return success_response("Attendance analytics", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Attendance analytics route error: {str(e)}")
        return error_response(str(e), 500)


# ==================== FEE ANALYTICS ====================

@analytics_bp.route('/fees', methods=['GET'])
@token_required
@permission_required('view_fee_analytics', 'view_analytics')
def fee_analytics(current_user):
    """Get fee collection analytics"""
    try:
        academic_year = request.args.get('academic_year')
        result = AnalyticsService.get_fee_analytics(
            current_user.school_id, academic_year
        )
        if result['success']:
            return success_response("Fee analytics", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Fee analytics route error: {str(e)}")
        return error_response(str(e), 500)
