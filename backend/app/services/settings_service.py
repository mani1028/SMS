"""
Settings Service - System configuration and audit management
"""

from app.models.settings import SchoolConfiguration, AcademicYear, AuditLog, SystemLog
from app.extensions import db
from datetime import datetime, date
import logging
import json

logger = logging.getLogger(__name__)


class SettingsService:
    """Service for school configuration"""
    
    @staticmethod
    def get_config(school_id):
        """Get school configuration"""
        try:
            config = SchoolConfiguration.query.filter_by(school_id=school_id).first()
            
            if not config:
                return {'success': False, 'error': 'Configuration not found'}
            
            return {'success': True, 'config': config.to_dict()}
        except Exception as e:
            logger.error(f"Error getting config: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def update_config(school_id, **kwargs):
        """Update school configuration"""
        try:
            config = SchoolConfiguration.query.filter_by(school_id=school_id).first()
            
            if not config:
                # Create default config
                config = SchoolConfiguration(
                    school_id=school_id,
                    school_name=kwargs.get('school_name', 'School')
                )
                db.session.add(config)
            
            allowed_fields = [
                'academic_year', 'class_start_time', 'class_end_time',
                'lunch_break_start', 'lunch_break_end', 'school_days',
                'currency_symbol', 'tax_rate', 'standard_fine_per_day',
                'attendance_marking_enabled', 'subject_wise_attendance',
                'grading_scale', 'email_notifications_enabled',
                'sms_notifications_enabled', 'email_gateway_api_key',
                'sms_gateway_api_key', 'school_name', 'school_logo_url',
                'school_address', 'school_phone', 'school_email',
                'school_website', 'primary_color', 'secondary_color',
                'enable_transport', 'gps_tracking_enabled', 'enable_hostel',
                'enable_library', 'book_issue_limit', 'book_issue_days',
                'payment_gateway', 'payment_gateway_key',
                'session_timeout_minutes', 'require_password_change_days',
                'enable_demo_data', 'enable_backup', 'backup_frequency'
            ]
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(config, field, value)
            
            db.session.commit()
            return {'success': True, 'config': config.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating config: {str(e)}")
            return {'success': False, 'error': str(e)}


class AcademicYearService:
    """Service for academic year management"""
    
    @staticmethod
    def create_academic_year(school_id, year, start_date, end_date, is_current=False, description=None):
        """Create academic year"""
        try:
            existing = AcademicYear.query.filter_by(school_id=school_id, year=year).first()
            if existing:
                return {'success': False, 'error': 'Academic year already exists'}
            
            # If marking as current, unmark others
            if is_current:
                AcademicYear.query.filter_by(school_id=school_id, is_current=True).update({'is_current': False})
            
            academic_year = AcademicYear(
                school_id=school_id,
                year=year,
                start_date=start_date,
                end_date=end_date,
                is_current=is_current,
                is_active=True,
                description=description
            )
            db.session.add(academic_year)
            db.session.commit()
            
            return {'success': True, 'academic_year': academic_year.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating academic year: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_academic_years(school_id, page=1, limit=50):
        """Get academic years"""
        try:
            query = AcademicYear.query.filter_by(school_id=school_id)
            total = query.count()
            pages = (total + limit - 1) // limit
            
            years = query.offset((page - 1) * limit).limit(limit).order_by(
                AcademicYear.start_date.desc()
            ).all()
            
            return {
                'success': True,
                'years': [y.to_dict() for y in years],
                'total': total,
                'pages': pages
            }
        except Exception as e:
            logger.error(f"Error getting academic years: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def set_current_academic_year(school_id, academic_year_id):
        """Set current academic year"""
        try:
            # Unmark all others
            AcademicYear.query.filter_by(school_id=school_id).update({'is_current': False})
            
            # Mark this one
            year = AcademicYear.query.filter_by(id=academic_year_id, school_id=school_id).first()
            if not year:
                return {'success': False, 'error': 'Academic year not found'}
            
            year.is_current = True
            db.session.commit()
            
            return {'success': True, 'academic_year': year.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error setting current year: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_current_academic_year(school_id):
        """Get current academic year"""
        try:
            year = AcademicYear.query.filter_by(school_id=school_id, is_current=True).first()
            
            if not year:
                return {'success': False, 'error': 'No current academic year set'}
            
            return {'success': True, 'academic_year': year.to_dict()}
        except Exception as e:
            logger.error(f"Error getting current year: {str(e)}")
            return {'success': False, 'error': str(e)}


class AuditService:
    """Service for audit logging"""
    
    @staticmethod
    def log_action(school_id, user_id, action, entity_type, entity_id=None, 
                  old_values=None, new_values=None, ip_address=None):
        """Log an action"""
        try:
            log = AuditLog(
                school_id=school_id,
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                old_values=json.dumps(old_values) if old_values else None,
                new_values=json.dumps(new_values) if new_values else None,
                timestamp=datetime.utcnow(),
                ip_address=ip_address
            )
            db.session.add(log)
            db.session.commit()
            
            return {'success': True, 'log': log.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error logging action: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_audit_logs(school_id, user_id=None, entity_type=None, from_date=None, 
                      to_date=None, page=1, limit=50):
        """Get audit logs"""
        try:
            query = AuditLog.query.filter_by(school_id=school_id)
            
            if user_id:
                query = query.filter_by(user_id=user_id)
            if entity_type:
                query = query.filter_by(entity_type=entity_type)
            if from_date:
                query = query.filter(AuditLog.timestamp >= from_date)
            if to_date:
                query = query.filter(AuditLog.timestamp <= to_date)
            
            total = query.count()
            pages = (total + limit - 1) // limit
            
            logs = query.offset((page - 1) * limit).limit(limit).order_by(
                AuditLog.timestamp.desc()
            ).all()
            
            return {
                'success': True,
                'logs': [l.to_dict() for l in logs],
                'total': total,
                'pages': pages
            }
        except Exception as e:
            logger.error(f"Error getting audit logs: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_user_actions(school_id, user_id, day_limit=7):
        """Get recent actions by a user"""
        try:
            from datetime import timedelta
            
            since = datetime.utcnow() - timedelta(days=day_limit)
            logs = AuditLog.query.filter(
                AuditLog.school_id == school_id,
                AuditLog.user_id == user_id,
                AuditLog.timestamp >= since
            ).order_by(AuditLog.timestamp.desc()).all()
            
            return {'success': True, 'actions': [l.to_dict() for l in logs]}
        except Exception as e:
            logger.error(f"Error getting user actions: {str(e)}")
            return {'success': False, 'error': str(e)}


class SystemLogService:
    """Service for system logging"""
    
    @staticmethod
    def log_system_event(school_id, log_level, message, module=None):
        """Log a system event"""
        try:
            log = SystemLog(
                school_id=school_id,
                log_level=log_level,
                message=message,
                module=module,
                timestamp=datetime.utcnow()
            )
            db.session.add(log)
            db.session.commit()
            
            return {'success': True, 'log': log.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error logging system event: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_system_logs(school_id, log_level=None, module=None, from_date=None, 
                       to_date=None, page=1, limit=50):
        """Get system logs"""
        try:
            query = SystemLog.query.filter_by(school_id=school_id)
            
            if log_level:
                query = query.filter_by(log_level=log_level)
            if module:
                query = query.filter_by(module=module)
            if from_date:
                query = query.filter(SystemLog.timestamp >= from_date)
            if to_date:
                query = query.filter(SystemLog.timestamp <= to_date)
            
            total = query.count()
            pages = (total + limit - 1) // limit
            
            logs = query.offset((page - 1) * limit).limit(limit).order_by(
                SystemLog.timestamp.desc()
            ).all()
            
            return {
                'success': True,
                'logs': [l.to_dict() for l in logs],
                'total': total,
                'pages': pages
            }
        except Exception as e:
            logger.error(f"Error getting system logs: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_error_logs(school_id):
        """Get recent error logs"""
        try:
            logs = SystemLog.query.filter_by(
                school_id=school_id,
                log_level='ERROR'
            ).order_by(SystemLog.timestamp.desc()).limit(100).all()
            
            return {'success': True, 'errors': [l.to_dict() for l in logs]}
        except Exception as e:
            logger.error(f"Error getting error logs: {str(e)}")
            return {'success': False, 'error': str(e)}
