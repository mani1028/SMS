"""
Enquiry Routes
API endpoints for lead and enquiry management
"""
from flask import Blueprint, request, jsonify
from app.core.rbac import requires_roles
from app.core.response import success_response, error_response
from app.services.enquiry_service import EnquiryService
from app.core.validators import InputValidator, ValidationError

enquiry_bp = Blueprint('enquiry', __name__, url_prefix='/enquiries')


@enquiry_bp.route('', methods=['POST'])
@requires_roles('Admin', 'Admissions Officer', 'Staff')
def create_enquiry(current_user):
    """Create a new enquiry/lead"""
    try:
        data = request.get_json()
        school_id = current_user.school_id
        user_id = current_user.id
        
        # Validate required fields
        required = ['student_name', 'parent_name', 'parent_phone', 'class_applying_for']
        InputValidator.validate_required_fields(data, required)
        
        enquiry = EnquiryService.create_enquiry(school_id, data, user_id)
        
        return success_response(
            data=enquiry.to_dict(),
            message="Enquiry created successfully",
            status_code=201
        )
    except ValidationError as ve:
        return error_response(str(ve), 400)
    except Exception as e:
        return error_response(str(e), 500)


@enquiry_bp.route('', methods=['GET'])
@requires_roles('Admin', 'Admissions Officer', 'Staff')
def get_enquiries(current_user):
    """Get all enquiries with filters"""
    try:
        school_id = current_user.school_id
        user_id = current_user.id
        
        # Get query parameters for filtering
        filters = {
            'status': request.args.get('status'),
            'source': request.args.get('source'),
            'priority': request.args.get('priority'),
            'assigned_to': request.args.get('assigned_to', type=int),
            'class_applying_for': request.args.get('class'),
            'search': request.args.get('search'),
            'follow_up_due': request.args.get('follow_up_due', type=bool)
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        result = EnquiryService.get_enquiries(school_id, filters, page, per_page)
        
        return success_response(data=result)
        
    except Exception as e:
        return error_response(str(e), 500)


@enquiry_bp.route('/<int:enquiry_id>', methods=['GET'])
@requires_roles('Admin', 'Admissions Officer', 'Staff')
def get_enquiry(current_user, enquiry_id):
    """Get single enquiry by ID"""
    try:
        school_id = current_user.school_id
        user_id = current_user.id
        
        enquiry = EnquiryService.get_enquiry_by_id(school_id, enquiry_id)
        if not enquiry:
            return error_response("Enquiry not found", 404)
        
        return success_response(data=enquiry.to_dict())
        
    except Exception as e:
        return error_response(str(e), 500)


@enquiry_bp.route('/<int:enquiry_id>', methods=['PUT'])
@requires_roles('Admin', 'Admissions Officer', 'Staff')
def update_enquiry(current_user, enquiry_id):
    """Update enquiry details"""
    try:
        data = request.get_json()
        school_id = current_user.school_id
        user_id = current_user.id
        
        enquiry = EnquiryService.update_enquiry(school_id, enquiry_id, data, user_id)
        if not enquiry:
            return error_response("Enquiry not found", 404)
        
        return success_response(
            data=enquiry.to_dict(),
            message="Enquiry updated successfully"
        )
        
    except Exception as e:
        return error_response(str(e), 500)


@enquiry_bp.route('/<int:enquiry_id>', methods=['DELETE'])
@requires_roles('Admin')
def delete_enquiry(current_user, enquiry_id):
    """Delete an enquiry"""
    try:
        school_id = current_user.school_id
        user_id = current_user.id
        
        success = EnquiryService.delete_enquiry(school_id, enquiry_id, user_id)
        if not success:
            return error_response("Enquiry not found", 404)
        
        return success_response(message="Enquiry deleted successfully")
        
    except Exception as e:
        return error_response(str(e), 500)


@enquiry_bp.route('/<int:enquiry_id>/follow-ups', methods=['POST'])
@requires_roles('Admin', 'Admissions Officer', 'Staff')
def add_follow_up(current_user, enquiry_id):
    """Add a follow-up activity"""
    try:
        data = request.get_json()
        school_id = current_user.school_id
        user_id = current_user.id
        
        # Validate required fields
        required = ['follow_up_type', 'notes']
        InputValidator.validate_required_fields(data, required)
        
        follow_up = EnquiryService.add_follow_up(school_id, enquiry_id, data, user_id)
        if not follow_up:
            return error_response("Enquiry not found", 404)
        
        return success_response(
            data=follow_up.to_dict(),
            message="Follow-up added successfully",
            status_code=201
        )
    except ValidationError as ve:
        return error_response(str(ve), 400)
    except Exception as e:
        return error_response(str(e), 500)


@enquiry_bp.route('/<int:enquiry_id>/follow-ups', methods=['GET'])
@requires_roles('Admin', 'Admissions Officer', 'Staff')
def get_follow_ups(current_user, enquiry_id):
    """Get all follow-ups for an enquiry"""
    try:
        school_id = current_user.school_id
        user_id = current_user.id
        
        follow_ups = EnquiryService.get_follow_ups(school_id, enquiry_id)
        
        return success_response(
            data=[f.to_dict() for f in follow_ups]
        )
        
    except Exception as e:
        return error_response(str(e), 500)


@enquiry_bp.route('/dashboard', methods=['GET'])
@requires_roles('Admin', 'Admissions Officer')
def get_dashboard(current_user):
    """Get enquiry dashboard statistics"""
    try:
        school_id = current_user.school_id
        
        stats = EnquiryService.get_dashboard_stats(school_id)
        
        return success_response(data=stats)
        
    except Exception as e:
        return error_response(str(e), 500)


@enquiry_bp.route('/<int:enquiry_id>/convert', methods=['POST'])
@requires_roles('Admin', 'Admissions Officer')
def convert_to_student(current_user, enquiry_id):
    """Convert enquiry to admitted student"""
    try:
        data = request.get_json()
        school_id = current_user.school_id
        user_id = current_user.id
        
        student_id = data.get('student_id')
        if not student_id:
            return error_response("student_id is required", 400)
        
        enquiry = EnquiryService.convert_to_student(school_id, enquiry_id, student_id, user_id)
        if not enquiry:
            return error_response("Enquiry not found", 404)
        
        return success_response(
            data=enquiry.to_dict(),
            message="Enquiry converted to student successfully"
        )
        
    except Exception as e:
        return error_response(str(e), 500)


@enquiry_bp.route('/stats/pipeline', methods=['GET'])
@requires_roles('Admin', 'Admissions Officer')
def get_pipeline_stats(current_user):
    """Get pipeline funnel statistics"""
    try:
        school_id = current_user.school_id
        
        stats = EnquiryService.get_dashboard_stats(school_id)
        
        # Calculate pipeline funnel
        status_breakdown = stats.get('status_breakdown', {})
        
        pipeline = {
            'new_leads': status_breakdown.get('new', 0),
            'contacted': status_breakdown.get('contacted', 0),
            'visited': status_breakdown.get('visited', 0),
            'applied': status_breakdown.get('applied', 0),
            'document_pending': status_breakdown.get('document_pending', 0),
            'admitted': status_breakdown.get('admitted', 0),
            'rejected': status_breakdown.get('rejected', 0),
            'lost': status_breakdown.get('lost', 0)
        }
        
        return success_response(data={
            'pipeline': pipeline,
            'conversion_rate': stats.get('conversion_rate', 0),
            'follow_ups_due': stats.get('follow_ups_due', 0)
        })
        
    except Exception as e:
        return error_response(str(e), 500)
