"""
Curriculum Planner Service
Plan weekly/monthly syllabus, track topic progress
"""
from app.extensions import db
from app.models.curriculum import CurriculumPlan, CurriculumChapter, TopicProgress, WeeklySyllabus
from datetime import datetime, date, timedelta
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)


class CurriculumService:
    """Service for curriculum planning and tracking"""

    # ── Curriculum Plan CRUD ───────────────────────────────────

    @staticmethod
    def create_plan(school_id, teacher_id, class_id, subject_id, academic_year,
                    title, description=None, chapters=None):
        try:
            plan = CurriculumPlan(
                school_id=school_id,
                class_id=class_id,
                subject_id=subject_id,
                teacher_id=teacher_id,
                academic_year=academic_year,
                title=title,
                description=description,
                status='draft'
            )
            db.session.add(plan)
            db.session.flush()

            # Add chapters if provided
            if chapters:
                for idx, ch in enumerate(chapters, 1):
                    chapter = CurriculumChapter(
                        school_id=school_id,
                        plan_id=plan.id,
                        order_number=idx,
                        title=ch.get('title'),
                        description=ch.get('description'),
                        estimated_periods=ch.get('estimated_periods', 1),
                        start_date=datetime.strptime(ch['start_date'], '%Y-%m-%d').date() if ch.get('start_date') else None,
                        end_date=datetime.strptime(ch['end_date'], '%Y-%m-%d').date() if ch.get('end_date') else None
                    )
                    db.session.add(chapter)
                    db.session.flush()

                    # Add topics within chapter
                    if ch.get('topics'):
                        for t_idx, topic in enumerate(ch['topics'], 1):
                            tp = TopicProgress(
                                school_id=school_id,
                                chapter_id=chapter.id,
                                order_number=t_idx,
                                title=topic.get('title'),
                                description=topic.get('description'),
                                periods_required=topic.get('periods_required', 1),
                                planned_date=datetime.strptime(topic['planned_date'], '%Y-%m-%d').date() if topic.get('planned_date') else None,
                                teaching_method=topic.get('teaching_method')
                            )
                            db.session.add(tp)

                plan.total_chapters = len(chapters)

            db.session.commit()
            return {'success': True, 'data': plan.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Create plan error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_plans(school_id, teacher_id=None, class_id=None, subject_id=None,
                  academic_year=None, status=None):
        try:
            query = CurriculumPlan.query.filter_by(school_id=school_id)
            if teacher_id:
                query = query.filter_by(teacher_id=teacher_id)
            if class_id:
                query = query.filter_by(class_id=class_id)
            if subject_id:
                query = query.filter_by(subject_id=subject_id)
            if academic_year:
                query = query.filter_by(academic_year=academic_year)
            if status:
                query = query.filter_by(status=status)

            plans = query.order_by(CurriculumPlan.created_at.desc()).all()
            return {'success': True, 'data': [p.to_dict() for p in plans]}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_plan_detail(school_id, plan_id):
        try:
            plan = CurriculumPlan.query.filter_by(school_id=school_id, id=plan_id).first()
            if not plan:
                return {'success': False, 'error': 'Plan not found'}
            return {'success': True, 'data': plan.to_dict()}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def activate_plan(school_id, plan_id):
        try:
            plan = CurriculumPlan.query.filter_by(school_id=school_id, id=plan_id).first()
            if not plan:
                return {'success': False, 'error': 'Plan not found'}
            plan.status = 'active'
            db.session.commit()
            return {'success': True, 'message': 'Plan activated'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    # ── Topic Progress Tracking ────────────────────────────────

    @staticmethod
    def update_topic_progress(school_id, topic_id, **kwargs):
        try:
            topic = TopicProgress.query.filter_by(school_id=school_id, id=topic_id).first()
            if not topic:
                return {'success': False, 'error': 'Topic not found'}

            for key, value in kwargs.items():
                if hasattr(topic, key) and value is not None:
                    if key in ('planned_date', 'actual_date') and isinstance(value, str):
                        value = datetime.strptime(value, '%Y-%m-%d').date()
                    setattr(topic, key, value)

            db.session.commit()

            # Auto-update chapter status
            chapter = topic.chapter
            if chapter:
                all_topics = TopicProgress.query.filter_by(chapter_id=chapter.id).all()
                completed = sum(1 for t in all_topics if t.status == 'completed')
                if completed == len(all_topics):
                    chapter.status = 'completed'
                elif completed > 0:
                    chapter.status = 'in_progress'
                chapter.actual_periods = sum(t.periods_taken for t in all_topics)
                db.session.commit()

            return {'success': True, 'data': topic.to_dict()}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_teacher_progress_summary(school_id, teacher_id, academic_year=None):
        """Get overall curriculum progress for a teacher"""
        try:
            query = CurriculumPlan.query.filter_by(school_id=school_id, teacher_id=teacher_id)
            if academic_year:
                query = query.filter_by(academic_year=academic_year)

            plans = query.all()
            summary = []
            for plan in plans:
                summary.append({
                    'plan_id': plan.id,
                    'subject': plan.subject.name if plan.subject else None,
                    'class': plan.class_obj.name if plan.class_obj else None,
                    'completion_percentage': plan.get_completion_percentage(),
                    'total_chapters': len(plan.chapters),
                    'completed_chapters': sum(1 for ch in plan.chapters if ch.status == 'completed'),
                    'status': plan.status
                })

            return {'success': True, 'data': summary}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ── Weekly Syllabus ────────────────────────────────────────

    @staticmethod
    def create_weekly_syllabus(school_id, teacher_id, class_id, subject_id,
                                week_start_date, week_end_date, topics_planned,
                                section_id=None, homework=None):
        try:
            if isinstance(week_start_date, str):
                week_start_date = datetime.strptime(week_start_date, '%Y-%m-%d').date()
            if isinstance(week_end_date, str):
                week_end_date = datetime.strptime(week_end_date, '%Y-%m-%d').date()

            syllabus = WeeklySyllabus(
                school_id=school_id,
                teacher_id=teacher_id,
                class_id=class_id,
                section_id=section_id,
                subject_id=subject_id,
                week_start_date=week_start_date,
                week_end_date=week_end_date,
                topics_planned=topics_planned,
                homework=homework,
                status='planned'
            )
            db.session.add(syllabus)
            db.session.commit()
            return {'success': True, 'data': syllabus.to_dict()}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_weekly_syllabus(school_id, teacher_id=None, class_id=None,
                             week_start_date=None, subject_id=None):
        try:
            query = WeeklySyllabus.query.filter_by(school_id=school_id)
            if teacher_id:
                query = query.filter_by(teacher_id=teacher_id)
            if class_id:
                query = query.filter_by(class_id=class_id)
            if subject_id:
                query = query.filter_by(subject_id=subject_id)
            if week_start_date:
                if isinstance(week_start_date, str):
                    week_start_date = datetime.strptime(week_start_date, '%Y-%m-%d').date()
                query = query.filter_by(week_start_date=week_start_date)

            entries = query.order_by(WeeklySyllabus.week_start_date.desc()).all()
            return {'success': True, 'data': [e.to_dict() for e in entries]}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def update_weekly_syllabus(school_id, syllabus_id, **kwargs):
        try:
            syllabus = WeeklySyllabus.query.filter_by(school_id=school_id, id=syllabus_id).first()
            if not syllabus:
                return {'success': False, 'error': 'Syllabus entry not found'}

            for key, value in kwargs.items():
                if hasattr(syllabus, key) and value is not None:
                    setattr(syllabus, key, value)

            db.session.commit()
            return {'success': True, 'data': syllabus.to_dict()}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
