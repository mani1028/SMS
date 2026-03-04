"""Exams & Grading Routes - Stub for now"""
from flask import Blueprint, request
from app.core.auth import token_required, permission_required
from app.core.response import success_response, error_response

exam_bp = Blueprint('exams', __name__, url_prefix='/api/exams')

@exam_bp.route('/marks', methods=['POST'])
@token_required
@permission_required('enter_marks')
def enter_marks(current_user):
    """Enter marks for student"""
    try:
        data = request.get_json()
        return success_response("Marks entered", {"message": "Feature in development"})
    except Exception as e:
        return error_response(str(e), 500)

@exam_bp.route('/marks/student/<int:student_id>', methods=['GET'])
@token_required
@permission_required('view_grades', 'view_child_marks')
def get_student_marks(current_user, student_id):
    """Get student marks"""
    try:
        return success_response("Marks retrieved", {"marks": []})
    except Exception as e:
        return error_response(str(e), 500)
