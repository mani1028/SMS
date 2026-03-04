"""
Platform Management Routes
Super Admin operations for managing schools, subscriptions, and billing
"""
from flask import Blueprint, request, jsonify
from app.core.rbac import requires_roles
from app.core.auth import token_required
from app.core.response import success_response, error_response
from app.services.platform_service import PlatformService
from app.core.validators import InputValidator, ValidationError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

platform_bp = Blueprint('platform', __name__)


# ===== SUPER ADMIN AUTHENTICATION =====

@platform_bp.route('/super-admin/login', methods=['POST'])
def super_admin_login():
    """Super admin login (separate from school login)"""
    try:
        from flask_jwt_extended import create_access_token
        from app.services.auth_service import AuthService
        
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        # Validate
        InputValidator.validate_email(email)
        if len(password) < 8:
            return error_response("Invalid credentials", 401)
        
        result = AuthService.super_admin_login(email, password)
        if result['success']:
            access_token = create_access_token(identity=str(result['user_id']))
            response_data = result['user']
            response_data['token'] = access_token
            return success_response("Super admin logged in successfully", response_data)
        else:
            return error_response(result['error'], 401)
    
    except Exception as e:
        logger.error(f"Super admin login error: {str(e)}")
        return error_response("Login failed", 500)


# ===== SCHOOL MANAGEMENT =====

@platform_bp.route('/schools', methods=['GET'])
@requires_roles('Super Admin')
def list_schools(current_user):
    """List all schools with pagination and filters"""
    try:
        # Verify is super admin
        if not current_user.is_super_admin:
            return error_response("Only super admins can access this", 403)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')  # active, inactive, suspended, trial
        search = request.args.get('search')  # Search by name or email
        
        result = PlatformService.list_schools(page=page, per_page=per_page, status=status, search=search)
        return success_response("Schools retrieved", result)
    
    except Exception as e:
        logger.error(f"Error listing schools: {str(e)}")
        return error_response(str(e), 500)


@platform_bp.route('/schools/<int:school_id>', methods=['GET'])
@requires_roles('Super Admin')
def get_school_details(current_user, school_id):
    """Get detailed information about a school"""
    try:
        if not current_user.is_super_admin:
            return error_response("Only super admins can access this", 403)
        
        result = PlatformService.get_school_details(school_id)
        return success_response("School details", result)
    
    except Exception as e:
        logger.error(f"Error getting school details: {str(e)}")
        return error_response(str(e), 500)


@platform_bp.route('/schools', methods=['POST'])
@requires_roles('Super Admin')
def create_school(current_user):
    """Create a new school (for manual onboarding)"""
    try:
        if not current_user.is_super_admin:
            return error_response("Only super admins can create schools", 403)
        
        data = request.get_json()
        school_name = data.get('school_name', '').strip()
        school_email = data.get('school_email', '').lower().strip()
        admin_name = data.get('admin_name', '').strip()
        admin_email = data.get('admin_email', '').lower().strip()
        admin_password = data.get('admin_password', '')
        plan_id = data.get('plan_id', 1)  # Free plan by default
        
        # Validate
        InputValidator.validate_string(school_name, 'school_name', min_length=3, max_length=255)
        InputValidator.validate_email(school_email)
        InputValidator.validate_string(admin_name, 'admin_name', min_length=2)
        InputValidator.validate_email(admin_email)
        InputValidator.validate_string(admin_password, 'admin_password', min_length=8)
        
        result = PlatformService.create_school(
            school_name=school_name,
            school_email=school_email,
            admin_name=admin_name,
            admin_email=admin_email,
            admin_password=admin_password,
            plan_id=plan_id
        )
        
        if result['success']:
            return success_response(result['message'], result['school'], 201)
        else:
            return error_response(result['error'], 400)
    
    except ValidationError as e:
        return error_response(str(e), 400)
    except Exception as e:
        logger.error(f"Error creating school: {str(e)}")
        return error_response(str(e), 500)


@platform_bp.route('/schools/<int:school_id>/status', methods=['PUT'])
@requires_roles('Super Admin')
def update_school_status(current_user, school_id):
    """Update school status (activate/deactivate/suspend)"""
    try:
        if not current_user.is_super_admin:
            return error_response("Only super admins can modify schools", 403)
        
        data = request.get_json()
        status = data.get('status')  # active, inactive, suspended, trial
        reason = data.get('reason')
        
        if status not in ['active', 'inactive', 'suspended', 'trial']:
            return error_response("Invalid status", 400)
        
        result = PlatformService.update_school_status(school_id, status, reason)
        if result['success']:
            return success_response(result['message'], result['school'])
        else:
            return error_response(result['error'], 404)
    
    except Exception as e:
        logger.error(f"Error updating school status: {str(e)}")
        return error_response(str(e), 500)


@platform_bp.route('/schools/<int:school_id>', methods=['DELETE'])
@requires_roles('Super Admin')
def delete_school(current_user, school_id):
    """Delete a school and all its data (cascade)"""
    try:
        if not current_user.is_super_admin:
            return error_response("Only super admins can delete schools", 403)
        
        # Require confirmation
        data = request.get_json()
        if not data.get('confirm_delete'):
            return error_response("Confirmation required: send {'confirm_delete': true}", 400)
        
        result = PlatformService.delete_school(school_id)
        if result['success']:
            return success_response("School deleted successfully")
        else:
            return error_response(result['error'], 404)
    
    except Exception as e:
        logger.error(f"Error deleting school: {str(e)}")
        return error_response(str(e), 500)


# ===== SUBSCRIPTION & BILLING =====

@platform_bp.route('/plans', methods=['GET'])
def list_plans():
    """List all available subscription plans (public)"""
    try:
        result = PlatformService.list_plans()
        return success_response("Plans retrieved", result)
    except Exception as e:
        logger.error(f"Error listing plans: {str(e)}")
        return error_response(str(e), 500)


@platform_bp.route('/schools/<int:school_id>/subscription', methods=['GET'])
@requires_roles('Super Admin')
def get_school_subscription(current_user, school_id):
    """Get subscription details for a school"""
    try:
        if not current_user.is_super_admin:
            return error_response("Only super admins can view subscriptions", 403)
        
        result = PlatformService.get_school_subscription(school_id)
        return success_response("Subscription details", result)
    
    except Exception as e:
        logger.error(f"Error getting subscription: {str(e)}")
        return error_response(str(e), 500)


@platform_bp.route('/schools/<int:school_id>/subscription/upgrade', methods=['POST'])
@requires_roles('Super Admin')
def upgrade_subscription(current_user, school_id):
    """Upgrade a school to a different plan"""
    try:
        if not current_user.is_super_admin:
            return error_response("Only super admins can manage subscriptions", 403)
        
        data = request.get_json()
        plan_id = data.get('plan_id')
        
        if not plan_id:
            return error_response("plan_id is required", 400)
        
        result = PlatformService.upgrade_subscription(school_id, plan_id)
        if result['success']:
            return success_response(result['message'], result['subscription'])
        else:
            return error_response(result['error'], 400)
    
    except Exception as e:
        logger.error(f"Error upgrading subscription: {str(e)}")
        return error_response(str(e), 500)


@platform_bp.route('/schools/<int:school_id>/usage', methods=['GET'])
@requires_roles('Super Admin')
def get_school_usage(current_user, school_id):
    """Get usage metrics for a school"""
    try:
        if not current_user.is_super_admin:
            return error_response("Only super admins can view usage", 403)
        
        result = PlatformService.get_school_usage(school_id)
        return success_response("Usage metrics", result)
    
    except Exception as e:
        logger.error(f"Error getting usage: {str(e)}")
        return error_response(str(e), 500)


@platform_bp.route('/billings', methods=['GET'])
@requires_roles('Super Admin')
def list_billings(current_user):
    """List all billings across all schools"""
    try:
        if not current_user.is_super_admin:
            return error_response("Only super admins can view billings", 403)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')  # pending, paid, failed, etc.
        
        result = PlatformService.list_billings(page=page, per_page=per_page, status=status)
        return success_response("Billings retrieved", result)
    
    except Exception as e:
        logger.error(f"Error listing billings: {str(e)}")
        return error_response(str(e), 500)


@platform_bp.route('/analytics/dashboard', methods=['GET'])
@token_required
def platform_analytics(current_user):
    """Get platform-wide analytics"""
    try:
        if not current_user.is_super_admin:
            return error_response("Only super admins can view analytics", 403)
        
        result = PlatformService.get_platform_analytics()
        return success_response("Platform analytics", result)
    
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        return error_response(str(e), 500)


@platform_bp.route('/subscriptions', methods=['GET'])
def get_subscriptions():
    from app.models.billing import Subscription, School
    subs = Subscription.query.all()
    data = []
    for sub in subs:
        school = School.query.get(sub.school_id)
        data.append({
            'id': sub.id,
            'school_name': school.name if school else 'N/A',
            'status': sub.status,
            'renewal_date': sub.renewal_date.isoformat() if sub.renewal_date else None,
            'auto_renew': sub.auto_renew
        })
    return jsonify({'status': True, 'data': {'subscriptions': data}})


@platform_bp.route('/subscriptions/<int:sub_id>/retry', methods=['POST'])
def retry_subscription_payment(sub_id):
    from app.services.subscription_automation_service import process_subscriptions
    from app.utils.logging import get_logger
    logger = get_logger("platform_api")
    process_subscriptions()  # For demo, just re-run the automation
    logger.info(f"Manual payment retry triggered for subscription {sub_id}")
    return jsonify({'status': True, 'message': 'Payment retry triggered.'})


@platform_bp.route('/webhook-logs', methods=['GET'])
def get_webhook_logs():
    from app.models.webhook_log import WebhookLog
    logs = WebhookLog.query.order_by(WebhookLog.created_at.desc()).limit(100).all()
    data = []
    for log in logs:
        data.append({
            'event_type': log.event_type,
            'created_at': log.created_at.isoformat() if log.created_at else '',
            'signature': log.signature,
            'payload': log.payload[:500] + ('...' if len(log.payload) > 500 else '')
        })
    return jsonify({'status': True, 'data': {'logs': data}})


@platform_bp.route('/plan-features', methods=['GET'])
def get_plan_features():
    from app.models.billing import Plan
    plans = Plan.query.all()
    data = []
    for plan in plans:
        data.append({
            'name': plan.name,
            'enabled_features': plan.enabled_features or {}
        })
    return jsonify({'status': True, 'data': {'plans': data}})


@platform_bp.route('/audit-logs', methods=['GET'])
def get_audit_logs():
    from app.models.platform_audit_log import PlatformAuditLog
    logs = PlatformAuditLog.query.order_by(PlatformAuditLog.created_at.desc()).limit(100).all()
    data = []
    for log in logs:
        data.append({
            'action_type': log.action_type,
            'actor_id': log.actor_id,
            'actor_role': log.actor_role,
            'school_id': log.school_id,
            'description': log.description,
            'ip_address': log.ip_address,
            'created_at': log.created_at.isoformat() if log.created_at else ''
        })
    return jsonify({'status': True, 'data': {'logs': data}})


@platform_bp.route('/email-logs', methods=['GET'])
def get_email_logs():
    from app.models.email_log import EmailLog
    logs = EmailLog.query.order_by(EmailLog.created_at.desc()).limit(100).all()
    data = []
    for log in logs:
        data.append({
            'to_email': log.to_email,
            'subject': log.subject,
            'template_name': log.template_name,
            'status': log.status,
            'created_at': log.created_at.isoformat() if log.created_at else ''
        })
    return jsonify({'status': True, 'data': {'logs': data}})


@platform_bp.route('/api-keys', methods=['GET'])
def get_api_keys():
    from app.models.api_key import ApiKey
    keys = ApiKey.query.order_by(ApiKey.created_at.desc()).limit(100).all()
    data = []
    for key in keys:
        data.append({
            'id': key.id,
            'key': key.key,
            'is_active': key.is_active,
            'usage_count': key.usage_count,
            'daily_limit': key.daily_limit,
            'created_at': key.created_at.isoformat() if key.created_at else ''
        })
    return jsonify({'status': True, 'data': {'keys': data}})


@platform_bp.route('/api-keys', methods=['POST'])
def create_api_key():
    from app.models.api_key import ApiKey
    from app.extensions import db
    # For demo, assign to school_id=1
    key = ApiKey(school_id=1)
    db.session.add(key)
    db.session.commit()
    return jsonify({'status': True, 'message': 'API key created.'})


@platform_bp.route('/api-keys/<int:key_id>', methods=['DELETE'])
def delete_api_key(key_id):
    from app.models.api_key import ApiKey
    from app.extensions import db
    key = ApiKey.query.get(key_id)
    if not key:
        return jsonify({'status': False, 'message': 'API key not found.'}), 404
    db.session.delete(key)
    db.session.commit()
    return jsonify({'status': True, 'message': 'API key deleted.'})


@platform_bp.route('/branding/<int:school_id>', methods=['GET'])
def get_branding(school_id):
    from app.models.school import School
    school = School.query.get(school_id)
    if not school:
        return jsonify({'status': False, 'message': 'School not found.'}), 404
    return jsonify({'status': True, 'data': {
        'logo_url': school.logo_url,
        'primary_color': school.primary_color,
        'custom_domain': school.custom_domain
    }})

@platform_bp.route('/branding/<int:school_id>', methods=['POST'])
def update_branding_api(school_id):
    from app.services.branding_service import update_branding
    data = request.get_json()
    ok = update_branding(
        school_id,
        logo_url=data.get('logo_url'),
        primary_color=data.get('primary_color'),
        custom_domain=data.get('custom_domain')
    )
    if ok:
        return jsonify({'status': True, 'message': 'Branding updated.'})
    else:
        return jsonify({'status': False, 'message': 'Failed to update branding.'}), 400


@platform_bp.route('/backups', methods=['GET'])
def get_backups():
    from app.models.base import BaseModel
    from app.services.backup_service import BackupRecord
    backups = BackupRecord.query.order_by(BackupRecord.completed_at.desc()).limit(100).all()
    data = [b.to_dict() for b in backups]
    return jsonify({'status': True, 'data': {'backups': data}})


@platform_bp.route('/backup/<int:school_id>', methods=['POST'])
def backup_school(school_id):
    from app.services.backup_service import backup_school_db, BackupRecord
    from app.extensions import db
    import os
    db_url = os.environ.get('DATABASE_URL')
    file_path = backup_school_db(school_id, db_url)
    if file_path:
        record = BackupRecord(
            school_id=school_id,
            backup_type='school_data',
            file_name=os.path.basename(file_path),
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            status='completed',
            completed_at=datetime.utcnow()
        )
        db.session.add(record)
        db.session.commit()
        return jsonify({'status': True, 'message': 'Backup completed.'})
    else:
        return jsonify({'status': False, 'message': 'Backup failed.'}), 500
