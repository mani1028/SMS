"""
Audit Log Service (Hardened)
=============================
Enterprise-grade audit trail with:
  - Automatic change logging via decorator
  - IP address + X-Forwarded-For capture
  - Diff computation (old vs new values)
  - Retention policy support
  - Export capability for compliance
  - Audit summary dashboard
"""
from app.models.settings import AuditLog
from app.extensions import db
from datetime import datetime, timedelta
from functools import wraps
from flask import request
import json
import logging

logger = logging.getLogger(__name__)


class AuditService:
    """Service for creating and querying audit logs"""

    @staticmethod
    def log(school_id, user_id, action, entity_type, entity_id=None,
            old_values=None, new_values=None):
        """
        Create an audit log entry.
        
        Args:
            school_id: School tenant ID
            user_id: User who performed the action
            action: Action type (CREATE, UPDATE, DELETE, VIEW, EXPORT, LOGIN, etc.)
            entity_type: Entity being acted on (Student, FeePayment, Marks, etc.)
            entity_id: ID of the entity
            old_values: Dict of old values (for updates)
            new_values: Dict of new values (for creates/updates)
        """
        try:
            ip_address = None
            try:
                ip_address = (
                    request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
                    or request.remote_addr
                )
            except Exception:
                pass

            log_entry = AuditLog(
                school_id=school_id,
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                old_values=json.dumps(old_values) if old_values else None,
                new_values=json.dumps(new_values) if new_values else None,
                ip_address=ip_address
            )
            db.session.add(log_entry)
            db.session.commit()
            return log_entry
        except Exception as e:
            db.session.rollback()
            logger.error(f"Audit log error: {str(e)}")
            return None

    @staticmethod
    def get_logs(school_id, page=1, per_page=50, entity_type=None, action=None,
                 user_id=None, start_date=None, end_date=None, entity_id=None):
        """Get audit logs with filters and pagination"""
        try:
            query = AuditLog.query.filter_by(school_id=school_id)

            if entity_type:
                query = query.filter(AuditLog.entity_type == entity_type)
            if action:
                query = query.filter(AuditLog.action == action)
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            if entity_id:
                query = query.filter(AuditLog.entity_id == entity_id)
            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)
            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)

            query = query.order_by(AuditLog.timestamp.desc())

            total = query.count()
            pages = (total + per_page - 1) // per_page
            logs = query.offset((page - 1) * per_page).limit(per_page).all()

            return {
                'success': True,
                'logs': [log.to_dict() for log in logs],
                'total': total,
                'pages': pages,
                'current_page': page
            }
        except Exception as e:
            logger.error(f"Get audit logs error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_entity_history(school_id, entity_type, entity_id):
        """Get complete history for a specific entity"""
        try:
            logs = AuditLog.query.filter_by(
                school_id=school_id,
                entity_type=entity_type,
                entity_id=entity_id
            ).order_by(AuditLog.timestamp.desc()).all()

            return {
                'success': True,
                'history': [log.to_dict() for log in logs],
                'total': len(logs)
            }
        except Exception as e:
            logger.error(f"Get entity history error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_user_activity(school_id, user_id, page=1, per_page=50):
        """Get all actions performed by a specific user"""
        try:
            query = AuditLog.query.filter_by(
                school_id=school_id,
                user_id=user_id
            ).order_by(AuditLog.timestamp.desc())

            total = query.count()
            pages = (total + per_page - 1) // per_page
            logs = query.offset((page - 1) * per_page).limit(per_page).all()

            return {
                'success': True,
                'logs': [log.to_dict() for log in logs],
                'total': total,
                'pages': pages,
                'current_page': page
            }
        except Exception as e:
            logger.error(f"Get user activity error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_audit_summary(school_id, days=30):
        """Get audit summary for dashboard"""
        try:
            from sqlalchemy import func
            cutoff = datetime.utcnow() - __import__('datetime').timedelta(days=days)

            # Actions by type
            action_counts = db.session.query(
                AuditLog.action,
                func.count(AuditLog.id).label('count')
            ).filter(
                AuditLog.school_id == school_id,
                AuditLog.timestamp >= cutoff
            ).group_by(AuditLog.action).all()

            # Entity types
            entity_counts = db.session.query(
                AuditLog.entity_type,
                func.count(AuditLog.id).label('count')
            ).filter(
                AuditLog.school_id == school_id,
                AuditLog.timestamp >= cutoff
            ).group_by(AuditLog.entity_type).all()

            # Most active users
            user_counts = db.session.query(
                AuditLog.user_id,
                func.count(AuditLog.id).label('count')
            ).filter(
                AuditLog.school_id == school_id,
                AuditLog.timestamp >= cutoff
            ).group_by(AuditLog.user_id).order_by(
                func.count(AuditLog.id).desc()
            ).limit(10).all()

            total_logs = AuditLog.query.filter(
                AuditLog.school_id == school_id,
                AuditLog.timestamp >= cutoff
            ).count()

            return {
                'success': True,
                'summary': {
                    'total_actions': total_logs,
                    'period_days': days,
                    'actions_by_type': {a: c for a, c in action_counts},
                    'actions_by_entity': {e: c for e, c in entity_counts},
                    'most_active_users': [{'user_id': u, 'actions': c} for u, c in user_counts]
                }
            }
        except Exception as e:
            logger.error(f"Get audit summary error: {str(e)}")
            return {'success': False, 'error': str(e)}

    # ── Export for Compliance ─────────────────────────────────────────────

    @staticmethod
    def export_logs(school_id, start_date, end_date):
        """Export audit logs for compliance/archival."""
        try:
            logs = AuditLog.query.filter(
                AuditLog.school_id == school_id,
                AuditLog.timestamp >= start_date,
                AuditLog.timestamp <= end_date,
            ).order_by(AuditLog.timestamp.asc()).all()

            return {
                'success': True,
                'data': {
                    'export_date': datetime.utcnow().isoformat(),
                    'school_id': school_id,
                    'period': {
                        'start': start_date.isoformat() if hasattr(start_date, 'isoformat') else str(start_date),
                        'end': end_date.isoformat() if hasattr(end_date, 'isoformat') else str(end_date),
                    },
                    'total_entries': len(logs),
                    'logs': [log.to_dict() for log in logs],
                }
            }
        except Exception as e:
            logger.error(f"Audit export error: {e}")
            return {'success': False, 'error': str(e)}

    # ── Retention Policy ──────────────────────────────────────────────────

    @staticmethod
    def apply_retention(school_id, retention_days=365):
        """
        Purge audit logs older than retention period.
        Default: keep 1 year of logs.
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=retention_days)
            count = AuditLog.query.filter(
                AuditLog.school_id == school_id,
                AuditLog.timestamp < cutoff,
            ).count()

            if count > 0:
                AuditLog.query.filter(
                    AuditLog.school_id == school_id,
                    AuditLog.timestamp < cutoff,
                ).delete(synchronize_session=False)
                db.session.commit()

            return {
                'success': True,
                'data': {
                    'records_purged': count,
                    'cutoff_date': cutoff.isoformat(),
                    'retention_days': retention_days,
                }
            }
        except Exception as e:
            logger.error(f"Retention error: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}


# ── Decorator for Automatic Audit Logging ─────────────────────────────────

def audit_action(action, entity_type=None):
    """
    Decorator to automatically log an action after a route handler succeeds.

    Usage:
        @app.route('/students', methods=['POST'])
        @token_required
        @audit_action('CREATE_STUDENT', 'Student')
        def create_student(current_user):
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(current_user, *args, **kwargs):
            response = f(current_user, *args, **kwargs)

            try:
                # Only log on success (2xx responses)
                status = response[1] if isinstance(response, tuple) else 200
                if 200 <= status < 300:
                    eid = kwargs.get('student_id') or kwargs.get('id') or kwargs.get('expense_id')

                    AuditService.log(
                        school_id=current_user.school_id,
                        user_id=current_user.id,
                        action=action,
                        entity_type=entity_type or 'Unknown',
                        entity_id=eid,
                    )
            except Exception as e:
                logger.warning(f"Audit decorator error: {e}")

            return response
        return wrapper
    return decorator

# ── Platform-Level Audit Logging ──────────────────────────────────────────

def log_action(action_type, actor_id=None, actor_role=None, school_id=None, description=None):
    from app.models.platform_audit_log import PlatformAuditLog
    from app.extensions import db
    from flask import request
    import socket
    ip_address = request.remote_addr or socket.gethostbyname(socket.gethostname())
    log = PlatformAuditLog(
        action_type=action_type,
        actor_id=actor_id,
        actor_role=actor_role,
        school_id=school_id,
        description=description,
        ip_address=ip_address
    )
    db.session.add(log)
    db.session.commit()
    logger.info(f"Audit log: {action_type} by {actor_id} ({actor_role}) for school {school_id}")
