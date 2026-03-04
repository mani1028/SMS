"""
Security Middleware
Super admin checks, tenant isolation, feature gating, rate limiting helpers
"""
from functools import wraps
from flask import request
from app.core.response import error_response
import logging

logger = logging.getLogger(__name__)


def super_admin_required(f):
    """
    Decorator to restrict endpoint to platform super admins only.
    Must be stacked AFTER @token_required.
    """
    @wraps(f)
    def decorated_function(current_user, *args, **kwargs):
        if not current_user.is_super_admin:
            logger.warning(f"Non-super-admin user {current_user.id} attempted super admin action")
            return error_response("Platform admin access required", 403)
        return f(current_user, *args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorator to restrict endpoint to school admins only.
    Allows super admins through as well.
    Must be stacked AFTER @token_required.
    """
    @wraps(f)
    def decorated_function(current_user, *args, **kwargs):
        if current_user.is_super_admin:
            return f(current_user, *args, **kwargs)
        if not current_user.role or current_user.role.name not in ('Admin', 'Principal'):
            logger.warning(f"User {current_user.id} attempted admin action without admin role")
            return error_response("Admin access required", 403)
        return f(current_user, *args, **kwargs)
    return decorated_function


def school_admin_or_permission(f):
    """
    Allow access if user is school Admin/Principal OR has the specific permission.
    This is a pass-through for admin roles that also respects permission_required on the same route.
    """
    @wraps(f)
    def decorated_function(current_user, *args, **kwargs):
        if current_user.is_super_admin:
            return f(current_user, *args, **kwargs)
        if current_user.role and current_user.role.name in ('Admin', 'Principal'):
            return f(current_user, *args, **kwargs)
        # Fall through to let permission_required handle it
        return f(current_user, *args, **kwargs)
    return decorated_function


def tenant_isolated(f):
    """
    Decorator that enforces tenant isolation by rejecting requests
    where user tries to access another school's data via URL params or body.
    Must be stacked AFTER @token_required.
    """
    @wraps(f)
    def decorated_function(current_user, *args, **kwargs):
        # Super admins can access any school
        if current_user.is_super_admin:
            return f(current_user, *args, **kwargs)

        # Check if school_id is in URL kwargs and doesn't match user's school
        if 'school_id' in kwargs:
            if kwargs['school_id'] != current_user.school_id:
                logger.warning(
                    f"Tenant isolation breach: User {current_user.id} (school {current_user.school_id}) "
                    f"tried accessing school {kwargs['school_id']}"
                )
                return error_response("Access denied: cross-tenant request", 403)

        # Check if school_id is in request body and doesn't match
        if request.is_json and request.get_json(silent=True):
            body_school_id = request.get_json(silent=True).get('school_id')
            if body_school_id and int(body_school_id) != current_user.school_id:
                logger.warning(
                    f"Tenant isolation breach: User {current_user.id} (school {current_user.school_id}) "
                    f"sent school_id={body_school_id} in body"
                )
                return error_response("Access denied: cross-tenant request", 403)

        return f(current_user, *args, **kwargs)
    return decorated_function


def feature_gate(feature_key):
    """
    Decorator that checks if a feature is enabled for the user's school.
    Must be stacked AFTER @token_required.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(current_user, *args, **kwargs):
            # Super admins bypass feature gates
            if current_user.is_super_admin:
                return f(current_user, *args, **kwargs)

            try:
                from app.services.feature_toggle_service import FeatureToggleService
                result = FeatureToggleService.check_feature_enabled(
                    school_id=current_user.school_id,
                    feature_key=feature_key
                )
                if result['success'] and not result['data'].get('enabled', False):
                    return error_response(
                        f"Feature '{feature_key}' is not enabled for your school. "
                        f"Please upgrade your plan or contact support.",
                        403
                    )
            except Exception as e:
                logger.error(f"Feature gate check failed for {feature_key}: {e}")
                # Fail-open: if feature check fails, allow access (don't block on errors)
                pass

            return f(current_user, *args, **kwargs)
        return decorated_function
    return decorator


def validate_json(*required_fields):
    """
    Decorator that validates request body contains required JSON fields.
    Must be applied after auth decorators.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return error_response("Request must be JSON", 400)

            data = request.get_json(silent=True)
            if not data:
                return error_response("Invalid JSON body", 400)

            missing = [field for field in required_fields if field not in data or data[field] is None]
            if missing:
                return error_response(f"Missing required fields: {', '.join(missing)}", 400)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def limit_request_size(max_items=1000):
    """
    Decorator to limit array size in request body to prevent DoS.
    Checks common array fields like 'students', 'records', 'student_ids', 'data', 'items'.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.is_json:
                data = request.get_json(silent=True)
                if data:
                    array_fields = ['students', 'records', 'student_ids', 'data',
                                    'items', 'staff_ids', 'installments_data']
                    for field in array_fields:
                        if field in data and isinstance(data[field], list):
                            if len(data[field]) > max_items:
                                return error_response(
                                    f"Request too large: '{field}' contains {len(data[field])} items "
                                    f"(max {max_items})",
                                    413
                                )
            return f(*args, **kwargs)
        return decorated_function
    return decorator
