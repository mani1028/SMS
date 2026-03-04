"""
Advanced Feature Routes
ID Cards, Bulk Promotion, Document Vault, API Keys, Custom Reports
"""
from flask import Blueprint, request
from app.core.auth import token_required, permission_required
from app.core.decorators.requires_feature import requires_feature
from app.core.response import success_response, error_response
from app.core.middleware import admin_required, limit_request_size
from app.services.advanced_services import (
    StudentIDCardService, PromotionService,
    DocumentVaultService, APIKeyService, ReportsService
)
import logging

logger = logging.getLogger(__name__)

advanced_bp = Blueprint('advanced', __name__, url_prefix='/advanced')


# ── Student ID Cards ───────────────────────────────────────

@advanced_bp.route('/id-cards/generate', methods=['POST'])
@token_required
@permission_required('generate_id_card')
@requires_feature('advanced_id_cards')
def generate_id_card(current_user):
    """Generate ID card for a single student"""
    try:
        data = request.get_json()
        result = StudentIDCardService.generate_id_card(
            school_id=current_user.school_id,
            student_id=data.get('student_id'),
            academic_year=data.get('academic_year'),
            template=data.get('template', 'default'),
            valid_until=data.get('valid_until')
        )
        if result['success']:
            return success_response("ID card generated", result['data'], 201)
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Generate ID card error: {str(e)}")
        return error_response(str(e), 500)


@advanced_bp.route('/id-cards/bulk-generate', methods=['POST'])
@token_required
@permission_required('generate_id_card')
@requires_feature('advanced_id_cards')
@limit_request_size(500)
def bulk_generate_id_cards(current_user):
    """Bulk generate ID cards for a class"""
    try:
        data = request.get_json()
        result = StudentIDCardService.bulk_generate_cards(
            school_id=current_user.school_id,
            class_id=data.get('class_id'),
            section_id=data.get('section_id'),
            academic_year=data.get('academic_year'),
            template=data.get('template', 'default')
        )
        if result['success']:
            return success_response(result['message'], result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Bulk generate ID cards error: {str(e)}")
        return error_response(str(e), 500)


@advanced_bp.route('/id-cards/verify/<string:qr_code>', methods=['GET'])
def verify_qr_scan(qr_code):
    """Verify student by QR code scan (public endpoint)"""
    try:
        result = StudentIDCardService.verify_qr_scan(qr_code)
        if result['success']:
            return success_response("Student verified", result['data'])
        return error_response(result.get('error', 'Invalid QR code'), 404)
    except Exception as e:
        logger.error(f"QR verify error: {str(e)}")
        return error_response(str(e), 500)


@advanced_bp.route('/id-cards/student/<int:student_id>', methods=['GET'])
@token_required
@permission_required('generate_id_card', 'view_students')
def get_student_cards(current_user, student_id):
    """Get all ID cards for a student"""
    try:
        result = StudentIDCardService.get_student_cards(
            current_user.school_id, student_id
        )
        if result['success']:
            return success_response("Student ID cards", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Get student cards error: {str(e)}")
        return error_response(str(e), 500)


# ── Bulk Promotion ─────────────────────────────────────────

@advanced_bp.route('/promotions', methods=['POST'])
@token_required
@permission_required('manage_promotions')
@requires_feature('bulk_promotion')
def create_promotion_batch(current_user):
    """Create a new promotion batch"""
    try:
        data = request.get_json()
        result = PromotionService.create_promotion_batch(
            school_id=current_user.school_id,
            academic_year=data.get('academic_year'),
            from_class_id=data.get('from_class_id'),
            to_class_id=data.get('to_class_id'),
            created_by=current_user.id,
            criteria=data.get('criteria', {})
        )
        if result['success']:
            return success_response("Promotion batch created", result['data'], 201)
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Create promotion batch error: {str(e)}")
        return error_response(str(e), 500)


@advanced_bp.route('/promotions/<int:batch_id>/execute', methods=['POST'])
@token_required
@permission_required('manage_promotions')
def execute_promotion(current_user, batch_id):
    """Execute a promotion batch"""
    try:
        result = PromotionService.execute_promotion(
            current_user.school_id, batch_id
        )
        if result['success']:
            return success_response(result['message'], result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Execute promotion error: {str(e)}")
        return error_response(str(e), 500)


@advanced_bp.route('/promotions/<int:batch_id>/rollback', methods=['POST'])
@token_required
@permission_required('manage_promotions')
def rollback_promotion(current_user, batch_id):
    """Rollback a promotion batch"""
    try:
        result = PromotionService.rollback_promotion(
            current_user.school_id, batch_id
        )
        if result['success']:
            return success_response(result['message'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Rollback promotion error: {str(e)}")
        return error_response(str(e), 500)


@advanced_bp.route('/promotions', methods=['GET'])
@token_required
@permission_required('manage_promotions', 'view_students')
def get_promotion_batches(current_user):
    """List all promotion batches"""
    try:
        result = PromotionService.get_promotion_batches(current_user.school_id)
        if result['success']:
            return success_response("Promotion batches", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Get promotion batches error: {str(e)}")
        return error_response(str(e), 500)


# ── Document Vault ─────────────────────────────────────────

@advanced_bp.route('/documents', methods=['POST'])
@token_required
@permission_required('manage_documents', 'upload_document')
def upload_document(current_user):
    """Upload a document to the vault"""
    try:
        data = request.get_json()
        result = DocumentVaultService.upload_document(
            school_id=current_user.school_id,
            uploaded_by=current_user.id,
            document_name=data.get('document_name'),
            document_type=data.get('document_type'),
            file_path=data.get('file_path'),
            file_size=data.get('file_size'),
            mime_type=data.get('mime_type'),
            owner_type=data.get('owner_type'),
            owner_id=data.get('owner_id'),
            category=data.get('category'),
            description=data.get('description'),
            is_confidential=data.get('is_confidential', False),
            expires_at=data.get('expires_at')
        )
        if result['success']:
            return success_response("Document uploaded", result['data'], 201)
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Upload document error: {str(e)}")
        return error_response(str(e), 500)


@advanced_bp.route('/documents', methods=['GET'])
@token_required
@permission_required('manage_documents', 'view_documents')
def get_documents(current_user):
    """List documents with filters"""
    try:
        result = DocumentVaultService.get_documents(
            school_id=current_user.school_id,
            owner_type=request.args.get('owner_type'),
            owner_id=request.args.get('owner_id', type=int),
            category=request.args.get('category'),
            page=request.args.get('page', 1, type=int),
            per_page=request.args.get('per_page', 20, type=int)
        )
        if result['success']:
            return success_response("Documents", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Get documents error: {str(e)}")
        return error_response(str(e), 500)


@advanced_bp.route('/documents/<int:doc_id>/verify', methods=['PUT'])
@token_required
@permission_required('manage_documents')
def verify_document(current_user, doc_id):
    """Mark a document as verified"""
    try:
        result = DocumentVaultService.verify_document(
            current_user.school_id, doc_id, current_user.id
        )
        if result['success']:
            return success_response("Document verified")
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Verify document error: {str(e)}")
        return error_response(str(e), 500)


@advanced_bp.route('/documents/<int:doc_id>', methods=['DELETE'])
@token_required
@permission_required('manage_documents')
def delete_document(current_user, doc_id):
    """Soft-delete a document"""
    try:
        result = DocumentVaultService.delete_document(
            current_user.school_id, doc_id
        )
        if result['success']:
            return success_response("Document deleted")
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Delete document error: {str(e)}")
        return error_response(str(e), 500)


@advanced_bp.route('/documents/expiring', methods=['GET'])
@token_required
@permission_required('manage_documents', 'view_documents')
def expiring_documents(current_user):
    """Get documents expiring within a number of days"""
    try:
        days = request.args.get('days', 30, type=int)
        result = DocumentVaultService.check_expiring_documents(
            current_user.school_id, days
        )
        if result['success']:
            return success_response("Expiring documents", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Expiring documents error: {str(e)}")
        return error_response(str(e), 500)


# ── API Keys ──────────────────────────────────────────────

@advanced_bp.route('/api-keys', methods=['POST'])
@token_required
@permission_required('manage_api_keys')
def create_api_key(current_user):
    """Create a new API key for external access"""
    try:
        data = request.get_json()
        result = APIKeyService.create_api_key(
            school_id=current_user.school_id,
            name=data.get('name'),
            created_by=current_user.id,
            permissions=data.get('permissions', []),
            rate_limit=data.get('rate_limit', 1000),
            ip_whitelist=data.get('ip_whitelist'),
            expires_at=data.get('expires_at')
        )
        if result['success']:
            return success_response("API key created", result['data'], 201)
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Create API key error: {str(e)}")
        return error_response(str(e), 500)


@advanced_bp.route('/api-keys', methods=['GET'])
@token_required
@permission_required('manage_api_keys')
def list_api_keys(current_user):
    """List all API keys for the school"""
    try:
        result = APIKeyService.list_api_keys(current_user.school_id)
        if result['success']:
            return success_response("API keys", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"List API keys error: {str(e)}")
        return error_response(str(e), 500)


@advanced_bp.route('/api-keys/<int:key_id>/revoke', methods=['PUT'])
@token_required
@permission_required('manage_api_keys')
def revoke_api_key(current_user, key_id):
    """Revoke an API key"""
    try:
        result = APIKeyService.revoke_api_key(current_user.school_id, key_id)
        if result['success']:
            return success_response("API key revoked")
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Revoke API key error: {str(e)}")
        return error_response(str(e), 500)


# ── Custom Reports ─────────────────────────────────────────

@advanced_bp.route('/reports/student', methods=['GET'])
@token_required
@permission_required('view_reports', 'view_students')
def student_report(current_user):
    """Generate student report"""
    try:
        result = ReportsService.generate_student_report(
            school_id=current_user.school_id,
            class_id=request.args.get('class_id', type=int),
            section_id=request.args.get('section_id', type=int),
            academic_year=request.args.get('academic_year')
        )
        if result['success']:
            return success_response("Student report", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Student report error: {str(e)}")
        return error_response(str(e), 500)


@advanced_bp.route('/reports/fee', methods=['GET'])
@token_required
@permission_required('view_reports', 'collection_report')
def fee_report(current_user):
    """Generate fee collection report"""
    try:
        result = ReportsService.generate_fee_report(
            school_id=current_user.school_id,
            start_date=request.args.get('start_date'),
            end_date=request.args.get('end_date')
        )
        if result['success']:
            return success_response("Fee report", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Fee report error: {str(e)}")
        return error_response(str(e), 500)


@advanced_bp.route('/reports/attendance', methods=['GET'])
@token_required
@permission_required('view_reports', 'attendance_report')
def attendance_report(current_user):
    """Generate attendance report"""
    try:
        result = ReportsService.generate_attendance_report(
            school_id=current_user.school_id,
            class_id=request.args.get('class_id', type=int),
            month=request.args.get('month', type=int),
            year=request.args.get('year', type=int)
        )
        if result['success']:
            return success_response("Attendance report", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Attendance report error: {str(e)}")
        return error_response(str(e), 500)


@advanced_bp.route('/reports/exam', methods=['GET'])
@token_required
@permission_required('view_reports', 'view_grades')
def exam_report(current_user):
    """Generate exam report"""
    try:
        result = ReportsService.generate_exam_report(
            school_id=current_user.school_id,
            exam_id=request.args.get('exam_id', type=int)
        )
        if result['success']:
            return success_response("Exam report", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Exam report error: {str(e)}")
        return error_response(str(e), 500)


@advanced_bp.route('/reports/export', methods=['POST'])
@token_required
@permission_required('export_data')
def export_csv(current_user):
    """Export data as CSV"""
    try:
        data = request.get_json()
        result = ReportsService.export_csv_data(
            school_id=current_user.school_id,
            report_type=data.get('report_type'),
            filters=data.get('filters', {})
        )
        if result['success']:
            return success_response("CSV export", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Export CSV error: {str(e)}")
        return error_response(str(e), 500)
