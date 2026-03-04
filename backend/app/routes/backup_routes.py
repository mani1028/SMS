"""
Backup & Restore Routes
Create backups, restore, manage backup history
"""
from flask import Blueprint, request
from app.core.auth import token_required, permission_required
from app.core.response import success_response, error_response
from app.core.middleware import admin_required
from app.services.backup_service import BackupService
import logging

logger = logging.getLogger(__name__)

backup_bp = Blueprint('backups', __name__, url_prefix='/backups')


@backup_bp.route('', methods=['POST'])
@token_required
@admin_required
def create_backup(current_user):
    """Create a new backup"""
    try:
        data = request.get_json() or {}
        backup_type = data.get('backup_type', 'school_data')
        notes = data.get('notes')

        result = BackupService.create_backup(
            school_id=current_user.school_id,
            initiated_by_id=current_user.id,
            backup_type=backup_type,
            notes=notes
        )
        if result['success']:
            return success_response(result['message'], result['data'], 201)
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@backup_bp.route('', methods=['GET'])
@token_required
@admin_required
def list_backups(current_user):
    """List all backups"""
    try:
        result = BackupService.get_backups(
            school_id=current_user.school_id,
            page=request.args.get('page', 1, type=int),
            per_page=request.args.get('per_page', 20, type=int)
        )
        if result['success']:
            return success_response("Backups", result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@backup_bp.route('/<int:backup_id>/restore', methods=['POST'])
@token_required
@admin_required
def restore_backup(current_user, backup_id):
    """Restore from a backup (admin only, tenant-isolated)"""
    try:
        result = BackupService.restore_backup(
            backup_id=backup_id,
            school_id=current_user.school_id,
            initiated_by_id=current_user.id
        )
        if result['success']:
            return success_response(result['message'], result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@backup_bp.route('/<int:backup_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_backup(current_user, backup_id):
    """Delete a backup (admin only, tenant-isolated)"""
    try:
        result = BackupService.delete_backup(backup_id, school_id=current_user.school_id)
        if result['success']:
            return success_response(result['message'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)
