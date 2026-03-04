"""
Curriculum Planner Routes
Syllabus planning, topic tracking, weekly plans
"""
from flask import Blueprint, request
from app.core.auth import token_required, permission_required
from app.core.response import success_response, error_response
from app.services.curriculum_service import CurriculumService
import logging

logger = logging.getLogger(__name__)

curriculum_bp = Blueprint('curriculum', __name__, url_prefix='/curriculum')


# ── Curriculum Plans ───────────────────────────────────────

@curriculum_bp.route('/plans', methods=['POST'])
@token_required
@permission_required('create_curriculum')
def create_plan(current_user):
    try:
        data = request.get_json()
        result = CurriculumService.create_plan(
            school_id=current_user.school_id,
            teacher_id=data.get('teacher_id', current_user.id),
            class_id=data.get('class_id'),
            subject_id=data.get('subject_id'),
            academic_year=data.get('academic_year'),
            title=data.get('title'),
            description=data.get('description'),
            chapters=data.get('chapters')
        )
        if result['success']:
            return success_response("Plan created", result['data'], 201)
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@curriculum_bp.route('/plans', methods=['GET'])
@token_required
@permission_required('view_curriculum')
def get_plans(current_user):
    try:
        result = CurriculumService.get_plans(
            school_id=current_user.school_id,
            teacher_id=request.args.get('teacher_id', type=int),
            class_id=request.args.get('class_id', type=int),
            subject_id=request.args.get('subject_id', type=int),
            academic_year=request.args.get('academic_year'),
            status=request.args.get('status')
        )
        if result['success']:
            return success_response("Plans", result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@curriculum_bp.route('/plans/<int:plan_id>', methods=['GET'])
@token_required
@permission_required('view_curriculum')
def get_plan_detail(current_user, plan_id):
    try:
        result = CurriculumService.get_plan_detail(current_user.school_id, plan_id)
        if result['success']:
            return success_response("Plan detail", result['data'])
        return error_response(result.get('error'), 404)
    except Exception as e:
        return error_response(str(e), 500)


@curriculum_bp.route('/plans/<int:plan_id>/activate', methods=['PUT'])
@token_required
@permission_required('edit_curriculum')
def activate_plan(current_user, plan_id):
    try:
        result = CurriculumService.activate_plan(current_user.school_id, plan_id)
        if result['success']:
            return success_response(result['message'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


# ── Topic Progress ─────────────────────────────────────────

@curriculum_bp.route('/topics/<int:topic_id>', methods=['PUT'])
@token_required
@permission_required('edit_curriculum')
def update_topic(current_user, topic_id):
    try:
        data = request.get_json()
        result = CurriculumService.update_topic_progress(
            school_id=current_user.school_id,
            topic_id=topic_id,
            **data
        )
        if result['success']:
            return success_response("Topic updated", result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@curriculum_bp.route('/teacher/<int:teacher_id>/progress', methods=['GET'])
@token_required
@permission_required('view_curriculum')
def teacher_progress(current_user, teacher_id):
    try:
        result = CurriculumService.get_teacher_progress_summary(
            school_id=current_user.school_id,
            teacher_id=teacher_id,
            academic_year=request.args.get('academic_year')
        )
        if result['success']:
            return success_response("Teacher progress", result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


# ── Weekly Syllabus ────────────────────────────────────────

@curriculum_bp.route('/weekly', methods=['POST'])
@token_required
@permission_required('manage_weekly_syllabus', 'create_curriculum')
def create_weekly(current_user):
    try:
        data = request.get_json()
        result = CurriculumService.create_weekly_syllabus(
            school_id=current_user.school_id,
            teacher_id=data.get('teacher_id', current_user.id),
            class_id=data.get('class_id'),
            subject_id=data.get('subject_id'),
            week_start_date=data.get('week_start_date'),
            week_end_date=data.get('week_end_date'),
            topics_planned=data.get('topics_planned'),
            section_id=data.get('section_id'),
            homework=data.get('homework')
        )
        if result['success']:
            return success_response("Weekly syllabus created", result['data'], 201)
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@curriculum_bp.route('/weekly', methods=['GET'])
@token_required
@permission_required('view_curriculum', 'manage_weekly_syllabus')
def get_weekly(current_user):
    try:
        result = CurriculumService.get_weekly_syllabus(
            school_id=current_user.school_id,
            teacher_id=request.args.get('teacher_id', type=int),
            class_id=request.args.get('class_id', type=int),
            week_start_date=request.args.get('week_start_date'),
            subject_id=request.args.get('subject_id', type=int)
        )
        if result['success']:
            return success_response("Weekly syllabus", result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@curriculum_bp.route('/weekly/<int:syllabus_id>', methods=['PUT'])
@token_required
@permission_required('manage_weekly_syllabus', 'edit_curriculum')
def update_weekly(current_user, syllabus_id):
    try:
        data = request.get_json()
        result = CurriculumService.update_weekly_syllabus(
            school_id=current_user.school_id,
            syllabus_id=syllabus_id,
            **data
        )
        if result['success']:
            return success_response("Weekly syllabus updated", result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)
