import functools
from flask import request, jsonify
from app.models.api_key import ApiKey
from app.extensions import db
from app.utils.logging import get_logger

logger = get_logger("api_key")

def requires_api_key(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'status': False, 'message': 'API key required'}), 401
        key_obj = ApiKey.query.filter_by(key=api_key, is_active=True).first()
        if not key_obj:
            logger.warning(f"Invalid API key: {api_key}")
            return jsonify({'status': False, 'message': 'Invalid API key'}), 403
        if key_obj.usage_count >= key_obj.daily_limit:
            logger.warning(f"API key daily limit exceeded: {api_key}")
            return jsonify({'status': False, 'message': 'API key daily limit exceeded'}), 429
        key_obj.usage_count += 1
        db.session.commit()
        return f(*args, **kwargs)
    return wrapper
