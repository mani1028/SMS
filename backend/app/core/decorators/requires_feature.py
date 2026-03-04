import functools
from flask import request, jsonify, g
from app.models.billing import Subscription
from app.utils.logging import get_logger

logger = get_logger("feature_enforcement")

def requires_feature(feature_name):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            school_id = getattr(g, 'school_id', None) or request.headers.get('X-School-Id')
            if not school_id:
                logger.warning("School ID missing in request for feature enforcement.")
                return jsonify({'status': False, 'message': 'School ID required', 'data': {}}), 400
            sub = Subscription.query.filter_by(school_id=school_id).first()
            if not sub or not sub.plan or not sub.plan.enabled_features:
                logger.warning(f"No subscription or plan for school {school_id}")
                return jsonify({'status': False, 'message': 'No active subscription', 'data': {}}), 403
            enabled = sub.plan.enabled_features.get(feature_name)
            if not enabled:
                logger.error(f"Feature '{feature_name}' not enabled for school {school_id}")
                # Log feature violation here if needed
                return jsonify({'status': False, 'message': f'Feature "{feature_name}" not enabled for your plan', 'data': {}}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator
