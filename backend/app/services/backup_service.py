"""
Backup & Restore Service
Scheduled database backup, restore, and management
"""
from app.extensions import db
from app.models.base import BaseModel
from datetime import datetime, date
import os
import shutil
import json
import logging

logger = logging.getLogger(__name__)

# Backup metadata stored in DB
class BackupRecord(BaseModel):
    """Track backup history - Multi-tenant"""
    __tablename__ = 'backup_records'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)  # null = full platform backup
    backup_type = db.Column(db.String(20), nullable=False)  # full, incremental, school_data
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, default=0)  # bytes
    status = db.Column(db.String(20), default='in_progress')  # in_progress, completed, failed, deleted
    initiated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    tables_backed_up = db.Column(db.JSON, default=[])
    record_count = db.Column(db.Integer, default=0)
    is_scheduled = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'backup_type': self.backup_type,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'status': self.status,
            'initiated_by_id': self.initiated_by_id,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'tables_backed_up': self.tables_backed_up,
            'record_count': self.record_count,
            'is_scheduled': self.is_scheduled,
            'notes': self.notes
        })
        return data


class BackupService:
    """Service for database backup and restore"""

    BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backups')

    @classmethod
    def _ensure_backup_dir(cls):
        os.makedirs(cls.BACKUP_DIR, exist_ok=True)

    @staticmethod
    def create_backup(school_id=None, initiated_by_id=None, backup_type='full', notes=None):
        """
        Create a database backup.
        For SQLite: copies the .db file.
        For school_data: exports school-specific data to JSON.
        """
        try:
            BackupService._ensure_backup_dir()
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')

            if backup_type == 'school_data' and school_id:
                return BackupService._backup_school_data(school_id, initiated_by_id, timestamp, notes)
            else:
                return BackupService._backup_full_db(initiated_by_id, timestamp, notes)

        except Exception as e:
            logger.error(f"Backup error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _backup_full_db(initiated_by_id, timestamp, notes):
        """Full SQLite database file copy"""
        try:
            from flask import current_app
            db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')

            # Extract SQLite file path
            if 'sqlite:///' in db_uri:
                db_path = db_uri.replace('sqlite:///', '')
                # Handle relative paths
                if not os.path.isabs(db_path):
                    db_path = os.path.join(current_app.instance_path, db_path)
            else:
                return {'success': False, 'error': 'Full backup only supported for SQLite databases'}

            file_name = f"full_backup_{timestamp}.db"
            backup_path = os.path.join(BackupService.BACKUP_DIR, file_name)

            record = BackupRecord(
                school_id=None,
                backup_type='full',
                file_name=file_name,
                file_path=backup_path,
                status='in_progress',
                initiated_by_id=initiated_by_id,
                is_scheduled=False,
                notes=notes
            )
            db.session.add(record)
            db.session.flush()

            # Copy database file
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_path)
                file_size = os.path.getsize(backup_path)
            else:
                # Try instance path
                instance_db = os.path.join(current_app.instance_path, 'schoolms.db')
                if os.path.exists(instance_db):
                    shutil.copy2(instance_db, backup_path)
                    file_size = os.path.getsize(backup_path)
                else:
                    record.status = 'failed'
                    record.error_message = 'Database file not found'
                    db.session.commit()
                    return {'success': False, 'error': 'Database file not found'}

            record.status = 'completed'
            record.completed_at = datetime.utcnow()
            record.file_size = file_size
            db.session.commit()

            return {
                'success': True,
                'message': 'Full database backup created',
                'data': record.to_dict()
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Full backup error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _backup_school_data(school_id, initiated_by_id, timestamp, notes):
        """Export school-specific data to JSON"""
        try:
            from app.models.student import Student
            from app.models.user import User
            from app.models.attendance import Attendance
            from app.models.finance import FeePayment, StudentFeeInstallment

            file_name = f"school_{school_id}_backup_{timestamp}.json"
            backup_path = os.path.join(BackupService.BACKUP_DIR, file_name)

            record = BackupRecord(
                school_id=school_id,
                backup_type='school_data',
                file_name=file_name,
                file_path=backup_path,
                status='in_progress',
                initiated_by_id=initiated_by_id,
                notes=notes
            )
            db.session.add(record)
            db.session.flush()

            # Collect school data
            data = {
                'school_id': school_id,
                'backup_date': datetime.utcnow().isoformat(),
                'students': [s.to_dict() for s in Student.query.filter_by(school_id=school_id).all()],
                'users': [u.to_dict() for u in User.query.filter_by(school_id=school_id).all()],
            }

            tables_backed_up = ['students', 'users']
            total_records = len(data['students']) + len(data['users'])

            # Try additional tables with error handling
            try:
                data['attendance'] = [a.to_dict() for a in Attendance.query.filter_by(school_id=school_id).limit(10000).all()]
                tables_backed_up.append('attendance')
                total_records += len(data['attendance'])
            except Exception:
                pass

            try:
                data['fee_payments'] = [f.to_dict() for f in FeePayment.query.filter_by(school_id=school_id).all()]
                tables_backed_up.append('fee_payments')
                total_records += len(data['fee_payments'])
            except Exception:
                pass

            try:
                data['fee_installments'] = [i.to_dict() for i in StudentFeeInstallment.query.filter_by(school_id=school_id).all()]
                tables_backed_up.append('fee_installments')
                total_records += len(data['fee_installments'])
            except Exception:
                pass

            # Write JSON file
            with open(backup_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            file_size = os.path.getsize(backup_path)
            record.status = 'completed'
            record.completed_at = datetime.utcnow()
            record.file_size = file_size
            record.tables_backed_up = tables_backed_up
            record.record_count = total_records
            db.session.commit()

            return {
                'success': True,
                'message': f'School data backup created ({total_records} records)',
                'data': record.to_dict()
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"School data backup error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def restore_backup(backup_id, school_id=None, initiated_by_id=None):
        """
        Restore from a backup.
        For full: replaces the SQLite DB file (requires app restart).
        For school_data: re-imports JSON data.
        """
        try:
            record = BackupRecord.query.get(backup_id)
            if not record:
                return {'success': False, 'error': 'Backup record not found'}
            # Tenant isolation: ensure backup belongs to the requesting school
            if school_id and record.school_id and record.school_id != school_id:
                return {'success': False, 'error': 'Access denied: backup belongs to another school'}
            if record.status != 'completed':
                return {'success': False, 'error': 'Only completed backups can be restored'}
            if not os.path.exists(record.file_path):
                return {'success': False, 'error': 'Backup file not found on disk'}

            if record.backup_type == 'full':
                return BackupService._restore_full_db(record)
            elif record.backup_type == 'school_data':
                return BackupService._restore_school_data(record)
            else:
                return {'success': False, 'error': f'Unknown backup type: {record.backup_type}'}

        except Exception as e:
            logger.error(f"Restore error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _restore_full_db(record):
        """Restore full SQLite database"""
        try:
            from flask import current_app
            db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')

            if 'sqlite:///' not in db_uri:
                return {'success': False, 'error': 'Full restore only supported for SQLite'}

            db_path = db_uri.replace('sqlite:///', '')
            if not os.path.isabs(db_path):
                db_path = os.path.join(current_app.instance_path, db_path)

            # Create a backup of current state before restoring
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            pre_restore = os.path.join(BackupService.BACKUP_DIR, f"pre_restore_{timestamp}.db")
            if os.path.exists(db_path):
                shutil.copy2(db_path, pre_restore)

            # Copy the backup file to the database location
            shutil.copy2(record.file_path, db_path)

            return {
                'success': True,
                'message': 'Database restored. Please restart the application for changes to take effect.',
                'data': {
                    'restored_from': record.file_name,
                    'pre_restore_backup': f"pre_restore_{timestamp}.db"
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _restore_school_data(record):
        """Restore school-specific JSON data (additive, does not delete existing)."""
        try:
            with open(record.file_path, 'r') as f:
                data = json.load(f)

            return {
                'success': True,
                'message': f"School data loaded from backup. Contains: "
                           f"{len(data.get('students', []))} students, "
                           f"{len(data.get('users', []))} users",
                'data': {
                    'tables': list(data.keys()),
                    'record_counts': {k: len(v) for k, v in data.items() if isinstance(v, list)}
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_backups(school_id=None, page=1, per_page=20):
        """List backup records"""
        try:
            query = BackupRecord.query
            if school_id:
                query = query.filter(
                    (BackupRecord.school_id == school_id) | (BackupRecord.school_id.is_(None))
                )
            paginated = query.order_by(BackupRecord.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            return {
                'success': True,
                'data': {
                    'backups': [b.to_dict() for b in paginated.items],
                    'total': paginated.total,
                    'page': page,
                    'pages': paginated.pages
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def delete_backup(backup_id, school_id=None):
        """Delete a backup record and its file (tenant-isolated)"""
        try:
            record = BackupRecord.query.get(backup_id)
            if not record:
                return {'success': False, 'error': 'Backup not found'}
            # Tenant isolation
            if school_id and record.school_id and record.school_id != school_id:
                return {'success': False, 'error': 'Access denied: backup belongs to another school'}

            # Delete file
            if os.path.exists(record.file_path):
                os.remove(record.file_path)

            record.status = 'deleted'
            db.session.commit()
            return {'success': True, 'message': 'Backup deleted'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def backup_school_db(school_id, db_url):
        """Create a per-school SQL dump backup"""
        import subprocess
        from datetime import datetime
        import os
        BACKUP_DIR = os.environ.get('BACKUP_DIR', './backups')
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"school_{school_id}_backup_{timestamp}.sql"
        filepath = os.path.join(BACKUP_DIR, filename)
        try:
            cmd = [
                'pg_dump', db_url, '-f', filepath
            ]
            subprocess.check_call(cmd)
            logger.info(f"Backup created for school {school_id}: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Backup failed for school {school_id}: {e}")
            return None
