from flask import Blueprint
from app.services.dashboard_service import DashboardService
from app.services.activity_service import ActivityService
from app.core.response import success_response, error_response
from app.core.auth import token_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard/stats', methods=['GET'])
@token_required
def get_dashboard_stats(current_user):
    """Get dashboard statistics for the logged-in user's school"""
    try:
        result = DashboardService.get_stats(school_id=current_user.school_id)
        
        if result['success']:
            return success_response("Stats retrieved successfully", result['stats'])
        else:
            return error_response(result['error'], 400)
            
    except Exception as e:
        return error_response(f"Error retrieving dashboard stats: {str(e)}", 500)


@dashboard_bp.route('/dashboard/full', methods=['GET'])
@token_required
def get_full_dashboard(current_user):
    """Get comprehensive dashboard data including charts, trends, and activity"""
    try:
        result = DashboardService.get_full_dashboard_data(school_id=current_user.school_id)
        
        if result['success']:
            return success_response("Dashboard data retrieved successfully", result['data'])
        else:
            return error_response(result['error'], 400)
            
    except Exception as e:
        return error_response(f"Error retrieving dashboard data: {str(e)}", 500)


@dashboard_bp.route('/dashboard/trends', methods=['GET'])
@token_required
def get_enrollment_trends(current_user):
    """Get enrollment trends for the past 30 days"""
    try:
        result = ActivityService.get_enrollment_trends(school_id=current_user.school_id, days=30)
        
        if result['success']:
            return success_response("Enrollment trends retrieved successfully", result)
        else:
            return error_response(result['error'], 400)
            
    except Exception as e:
        return error_response(f"Error retrieving trends: {str(e)}", 500)


@dashboard_bp.route('/dashboard/classes', methods=['GET'])
@token_required
def get_class_distribution(current_user):
    """Get student distribution by class"""
    try:
        result = ActivityService.get_class_distribution(school_id=current_user.school_id)
        
        if result['success']:
            return success_response("Class distribution retrieved successfully", result)
        else:
            return error_response(result['error'], 400)
            
    except Exception as e:
        return error_response(f"Error retrieving class distribution: {str(e)}", 500)


@dashboard_bp.route('/dashboard/monthly', methods=['GET'])
@token_required
def get_monthly_stats(current_user):
    """Get monthly activity statistics"""
    try:
        result = ActivityService.get_monthly_stats(school_id=current_user.school_id)
        
        if result['success']:
            return success_response("Monthly stats retrieved successfully", result)
        else:
            return error_response(result['error'], 400)
            
    except Exception as e:
        return error_response(f"Error retrieving monthly stats: {str(e)}", 500)


@dashboard_bp.route('/dashboard/seed-activities', methods=['POST'])
@token_required
def seed_sample_activities(current_user):
    """Create sample activities for demo/testing purposes (Admin only)"""
    try:
        result = DashboardService.seed_sample_activities(school_id=current_user.school_id, user_id=current_user.id)
        
        if result['success']:
            return success_response("Sample activities created successfully", result)
        else:
            return error_response(result['error'], 400)
            
    except Exception as e:
        return error_response(f"Error creating sample activities: {str(e)}", 500)