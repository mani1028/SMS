"""Finance & Fee Routes - Stub for now"""
from flask import Blueprint, request
from app.core.auth import token_required, permission_required
from app.core.response import success_response, error_response

finance_bp = Blueprint('finance', __name__, url_prefix='/api/finance')

@finance_bp.route('/payments', methods=['POST'])
@token_required
@permission_required('process_payment', 'initiate_payment')
def process_payment(current_user):
    """Process payment"""
    try:
        data = request.get_json()
        return success_response("Payment processed", {"message": "Feature in development"})
    except Exception as e:
        return error_response(str(e), 500)

@finance_bp.route('/defaulters', methods=['GET'])
@token_required
@permission_required('view_defaulters', 'view_fees')
def get_defaulters(current_user):
    """Get defaulters list"""
    try:
        return success_response("Defaulters retrieved", {"defaulters": []})
    except Exception as e:
        return error_response(str(e), 500)
