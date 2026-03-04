"""
Branch Routes
Multi-branch management for school chains
"""
from flask import Blueprint, request
from app.core.auth import token_required, permission_required
from app.core.response import success_response, error_response
from app.core.middleware import admin_required
from app.services.advanced_services import BranchService
import logging

logger = logging.getLogger(__name__)

branch_bp = Blueprint('branches', __name__, url_prefix='/branches')


@branch_bp.route('', methods=['POST'])
@token_required
@permission_required('create_branch')
def create_branch(current_user):
    """Create a new branch"""
    try:
        data = request.get_json()
        result = BranchService.create_branch(
            school_id=current_user.school_id,
            name=data.get('name'),
            code=data.get('code'),
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state'),
            pincode=data.get('pincode'),
            phone=data.get('phone'),
            email=data.get('email'),
            principal_id=data.get('principal_id'),
            is_main=data.get('is_main', False),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            student_capacity=data.get('student_capacity')
        )
        if result['success']:
            return success_response("Branch created", result['data'], 201)
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Create branch error: {str(e)}")
        return error_response(str(e), 500)


@branch_bp.route('', methods=['GET'])
@token_required
@permission_required('view_branches')
def get_branches(current_user):
    """List all branches for the school"""
    try:
        result = BranchService.get_branches(current_user.school_id)
        if result['success']:
            return success_response("Branches list", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Get branches error: {str(e)}")
        return error_response(str(e), 500)


@branch_bp.route('/<int:branch_id>', methods=['GET'])
@token_required
@permission_required('view_branches')
def get_branch(current_user, branch_id):
    """Get single branch details"""
    try:
        result = BranchService.get_branch(current_user.school_id, branch_id)
        if result['success']:
            return success_response("Branch details", result['data'])
        return error_response(result.get('error', 'Error'), 404)
    except Exception as e:
        logger.error(f"Get branch error: {str(e)}")
        return error_response(str(e), 500)


@branch_bp.route('/<int:branch_id>', methods=['PUT'])
@token_required
@permission_required('edit_branch')
def update_branch(current_user, branch_id):
    """Update branch"""
    try:
        data = request.get_json()
        result = BranchService.update_branch(
            current_user.school_id, branch_id, data
        )
        if result['success']:
            return success_response("Branch updated", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Update branch error: {str(e)}")
        return error_response(str(e), 500)


@branch_bp.route('/<int:branch_id>', methods=['DELETE'])
@token_required
@permission_required('delete_branch')
def delete_branch(current_user, branch_id):
    """Deactivate a branch"""
    try:
        result = BranchService.delete_branch(current_user.school_id, branch_id)
        if result['success']:
            return success_response(result['message'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Delete branch error: {str(e)}")
        return error_response(str(e), 500)


@branch_bp.route('/<int:branch_id>/stats', methods=['GET'])
@token_required
@permission_required('view_branches', 'view_analytics')
def branch_stats(current_user, branch_id):
    """Get branch statistics"""
    try:
        result = BranchService.get_branch_stats(
            current_user.school_id, branch_id
        )
        if result['success']:
            return success_response("Branch stats", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Branch stats error: {str(e)}")
        return error_response(str(e), 500)
