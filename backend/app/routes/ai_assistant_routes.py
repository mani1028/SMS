"""
AI Parent Assistant Routes
===========================
Chat endpoint + quick suggestions for parent-facing AI chatbot.
"""
from flask import Blueprint, request
from app.core.auth import token_required, permission_required
from app.core.response import success_response, error_response
from app.services.ai_parent_assistant import AIParentAssistant
import logging

logger = logging.getLogger(__name__)

ai_assistant_bp = Blueprint('ai_assistant', __name__, url_prefix='/ai-assistant')


@ai_assistant_bp.route('/chat', methods=['POST'])
@token_required
@permission_required('view_child_overview', 'view_students')
def chat(current_user):
    """Send a message to the AI assistant and get a response."""
    try:
        data = request.get_json()
        if not data or not data.get('message'):
            return error_response("message is required", 400)

        student_id = data.get('student_id')
        if not student_id:
            return error_response("student_id is required", 400)

        result = AIParentAssistant.chat(
            school_id=current_user.school_id,
            parent_id=current_user.id,
            student_id=student_id,
            message=data['message']
        )

        return success_response("Response generated", result)
    except Exception as e:
        logger.error(f"AI chat error: {str(e)}")
        return error_response(str(e), 500)


@ai_assistant_bp.route('/suggestions/<int:student_id>', methods=['GET'])
@token_required
@permission_required('view_child_overview', 'view_students')
def get_suggestions(current_user, student_id):
    """Get contextual quick-action suggestions."""
    try:
        result = AIParentAssistant.get_suggestions(
            school_id=current_user.school_id,
            student_id=student_id
        )
        return success_response("Suggestions", result)
    except Exception as e:
        logger.error(f"AI suggestions error: {str(e)}")
        return error_response(str(e), 500)


@ai_assistant_bp.route('/history', methods=['GET'])
@token_required
@permission_required('view_child_overview')
def chat_history(current_user):
    """
    Get chat history (stub — stored client-side for now).
    Future: persist conversations server-side.
    """
    return success_response("Chat history", {"messages": [], "note": "History stored client-side"})
