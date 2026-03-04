"""
Custom Branding Routes
Logo, theme colors, school name, report headers
"""
from flask import Blueprint, request
from app.core.auth import token_required, permission_required
from app.core.response import success_response, error_response
from app.core.middleware import admin_required
from app.services.branding_service import BrandingService
import logging

logger = logging.getLogger(__name__)

branding_bp = Blueprint('branding', __name__, url_prefix='/branding')


@branding_bp.route('', methods=['GET'])
@token_required
@permission_required('view_branding', 'view_config')
def get_branding(current_user):
    """Get school branding configuration"""
    try:
        result = BrandingService.get_branding(current_user.school_id)
        if result['success']:
            return success_response("Branding", result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@branding_bp.route('', methods=['PUT'])
@token_required
@permission_required('edit_branding')
def update_branding(current_user):
    """Update school branding"""
    try:
        data = request.get_json()
        result = BrandingService.update_branding(
            school_id=current_user.school_id, **data
        )
        if result['success']:
            return success_response(result['message'], result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@branding_bp.route('/logo', methods=['PUT'])
@token_required
@permission_required('edit_branding')
def update_logo(current_user):
    """Update school logo URL"""
    try:
        data = request.get_json()
        result = BrandingService.upload_logo(
            school_id=current_user.school_id,
            logo_url=data.get('logo_url')
        )
        if result['success']:
            return success_response(result['message'], result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@branding_bp.route('/report-header', methods=['GET'])
@token_required
@permission_required('view_branding', 'view_config')
def get_report_header(current_user):
    """Get formatted branding for report headers"""
    try:
        result = BrandingService.get_report_header(current_user.school_id)
        if result['success']:
            return success_response("Report header", result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)
