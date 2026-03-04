"""
Feature Toggle Routes
Enable/disable modules per school plan, admin overrides, global kill switch
"""
from flask import Blueprint, request
from app.core.auth import token_required, permission_required
from app.core.response import success_response, error_response
from app.core.middleware import super_admin_required, admin_required, tenant_isolated
from app.services.feature_toggle_service import FeatureToggleService
import logging

logger = logging.getLogger(__name__)

feature_toggle_bp = Blueprint('feature_toggle', __name__, url_prefix='/features')


@feature_toggle_bp.route('/definitions', methods=['GET'])
@token_required
@super_admin_required
def get_all_features(current_user):
    """Get all feature definitions (platform admin only)"""
    try:
        result = FeatureToggleService.get_all_features()
        if result['success']:
            return success_response("Feature definitions", result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@feature_toggle_bp.route('', methods=['GET'])
@token_required
def get_school_features(current_user):
    """Get features enabled for the current school"""
    try:
        result = FeatureToggleService.get_school_features(current_user.school_id)
        if result['success']:
            return success_response("School features", result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@feature_toggle_bp.route('/check/<feature_key>', methods=['GET'])
@token_required
def check_feature(current_user, feature_key):
    """Quick check if a specific feature is enabled for this school"""
    try:
        result = FeatureToggleService.check_feature_enabled(
            school_id=current_user.school_id,
            feature_key=feature_key
        )
        if result['success']:
            return success_response("Feature status", result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@feature_toggle_bp.route('/toggle', methods=['POST'])
@token_required
@admin_required
@tenant_isolated
def toggle_feature(current_user):
    """Toggle a feature for own school (admin) or any school (super admin)"""
    try:
        data = request.get_json()
        # Non-super-admins can only toggle for their own school
        school_id = current_user.school_id
        if current_user.is_super_admin and data.get('school_id'):
            school_id = data.get('school_id')
        result = FeatureToggleService.toggle_feature(
            school_id=school_id,
            feature_key=data.get('feature_key'),
            enabled=data.get('enabled')
        )
        if result['success']:
            return success_response(result['message'], result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@feature_toggle_bp.route('/admin-override', methods=['POST'])
@token_required
@super_admin_required
def admin_override(current_user):
    """Platform admin: override a feature for a school regardless of plan"""
    try:
        data = request.get_json()
        result = FeatureToggleService.admin_override_feature(
            school_id=data.get('school_id'),
            feature_key=data.get('feature_key'),
            enabled=data.get('enabled')
        )
        if result['success']:
            return success_response(result['message'], result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@feature_toggle_bp.route('/global-toggle', methods=['POST'])
@token_required
@super_admin_required
def global_toggle(current_user):
    """Platform admin: enable/disable a feature globally (kill switch)"""
    try:
        data = request.get_json()
        result = FeatureToggleService.toggle_global_feature(
            feature_key=data.get('feature_key'),
            enabled=data.get('enabled')
        )
        if result['success']:
            return success_response(result['message'], result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@feature_toggle_bp.route('/seed', methods=['POST'])
@token_required
@super_admin_required
def seed_features(current_user):
    """Seed default feature definitions (platform admin only)"""
    try:
        result = FeatureToggleService.seed_feature_definitions()
        if result['success']:
            return success_response(result['message'], result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)
