from app.models.role import Role
from app.models.permission import Permission
from app.extensions import db
import logging

logger = logging.getLogger(__name__)


def initialize_rbac(school_id):
    """Initialize default RBAC for a school"""
    try:
        # Create default roles
        admin_role = Role.query.filter_by(school_id=school_id, name="Admin").first()
        if not admin_role:
            admin_role = Role(school_id=school_id, name="Admin")
            db.session.add(admin_role)
        
        teacher_role = Role.query.filter_by(school_id=school_id, name="Teacher").first()
        if not teacher_role:
            teacher_role = Role(school_id=school_id, name="Teacher")
            db.session.add(teacher_role)
        
        student_role = Role.query.filter_by(school_id=school_id, name="Student").first()
        if not student_role:
            student_role = Role(school_id=school_id, name="Student")
            db.session.add(student_role)
        
        db.session.commit()
        
        # Create default permissions
        permissions = [
            "view_students",
            "create_student",
            "edit_student",
            "delete_student",
            "view_parent",
            "create_parent",
            "edit_parent",
            "view_staff",
            "create_staff",
            "edit_staff",
            "manage_staff_attendance",
            "manage_staff_leaves",
            "view_dashboard",
            "view_reports",
            "manage_users",
            "manage_roles"
        ]
        
        for perm_name in permissions:
            perm = Permission.query.filter_by(name=perm_name).first()
            if not perm:
                perm = Permission(name=perm_name)
                db.session.add(perm)
        
        db.session.commit()
        
        # Assign all permissions to Admin role
        admin_perms = Permission.query.all()
        admin_role.permissions = admin_perms
        db.session.commit()
        
        logger.info(f"RBAC initialized for school {school_id}")
        return True
    except Exception as e:
        logger.error(f"RBAC initialization error: {str(e)}")
        db.session.rollback()
        return False


def has_permission(user, permission_name):
    """Check if user has specific permission"""
    if not user.role:
        return False
    
    permission = Permission.query.filter_by(name=permission_name).first()
    if not permission:
        return False
    
    return permission in user.role.permissions


def permission_required(permission_name):
    """Decorator to require specific permission for a route"""
    from functools import wraps
    from flask import jsonify
    from app.core.auth import token_required
    
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated_function(current_user, *args, **kwargs):
            if not has_permission(current_user, permission_name):
                return jsonify({
                    'success': False,
                    'message': f'Permission denied: {permission_name} required'
                }), 403
            return f(current_user, *args, **kwargs)
        return decorated_function
    return decorator


def requires_roles(*role_names):
    """Decorator to require specific roles for a route"""
    from functools import wraps
    from flask import jsonify
    from app.core.auth import token_required
    
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated_function(current_user, *args, **kwargs):
            # Allow superadmin even if no role object
            if getattr(current_user, 'is_super_admin', False):
                return f(current_user, *args, **kwargs)
            if not current_user.role:
                return jsonify({
                    'success': False,
                    'message': 'User has no role assigned'
                }), 403
            if current_user.role.name not in role_names:
                return jsonify({
                    'success': False,
                    'message': f'Access denied. Required roles: {", ".join(role_names)}'
                }), 403
            return f(current_user, *args, **kwargs)
        return decorated_function
    return decorator
