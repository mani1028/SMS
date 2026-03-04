"""
Curriculum Planner Models
Weekly/monthly syllabus planning, topic tracking for teachers
"""
from app.models.base import BaseModel
from app.extensions import db
from datetime import datetime


class CurriculumPlan(BaseModel):
    """Master curriculum plan for a subject/class - Multi-tenant"""
    __tablename__ = 'curriculum_plans'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    academic_year = db.Column(db.String(20), nullable=False)

    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    total_chapters = db.Column(db.Integer, default=0)
    total_periods = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='draft')  # draft, active, completed
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    class_obj = db.relationship('Class', foreign_keys=[class_id])
    subject = db.relationship('Subject', foreign_keys=[subject_id])
    teacher = db.relationship('User', foreign_keys=[teacher_id])
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])
    chapters = db.relationship('CurriculumChapter', backref='plan', cascade='all, delete-orphan',
                               order_by='CurriculumChapter.order_number')

    __table_args__ = (
        db.UniqueConstraint('school_id', 'class_id', 'subject_id', 'academic_year',
                            name='uq_curriculum_plan'),
    )

    def get_completion_percentage(self):
        if not self.chapters:
            return 0
        completed = sum(1 for ch in self.chapters if ch.status == 'completed')
        return round((completed / len(self.chapters)) * 100, 1)

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'class_id': self.class_id,
            'class_name': self.class_obj.name if self.class_obj else None,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else None,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.name if self.teacher else None,
            'academic_year': self.academic_year,
            'title': self.title,
            'description': self.description,
            'total_chapters': self.total_chapters,
            'total_periods': self.total_periods,
            'status': self.status,
            'completion_percentage': self.get_completion_percentage(),
            'chapters': [ch.to_dict() for ch in self.chapters] if self.chapters else []
        })
        return data


class CurriculumChapter(BaseModel):
    """Chapter/unit within a curriculum plan"""
    __tablename__ = 'curriculum_chapters'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('curriculum_plans.id'), nullable=False)
    order_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    estimated_periods = db.Column(db.Integer, default=1)
    actual_periods = db.Column(db.Integer, default=0)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='not_started')  # not_started, in_progress, completed

    # Relationships
    topics = db.relationship('TopicProgress', backref='chapter', cascade='all, delete-orphan',
                             order_by='TopicProgress.order_number')

    __table_args__ = (
        db.UniqueConstraint('plan_id', 'order_number', name='uq_chapter_order'),
    )

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'plan_id': self.plan_id,
            'order_number': self.order_number,
            'title': self.title,
            'description': self.description,
            'estimated_periods': self.estimated_periods,
            'actual_periods': self.actual_periods,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'topics': [t.to_dict() for t in self.topics] if self.topics else []
        })
        return data


class TopicProgress(BaseModel):
    """Individual topic within a chapter - tracks completion"""
    __tablename__ = 'topic_progress'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('curriculum_chapters.id'), nullable=False)
    order_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    periods_required = db.Column(db.Integer, default=1)
    periods_taken = db.Column(db.Integer, default=0)

    planned_date = db.Column(db.Date, nullable=True)
    actual_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, skipped

    teaching_method = db.Column(db.String(100))  # lecture, activity, lab, etc.
    resources = db.Column(db.Text)  # links, materials
    homework_assigned = db.Column(db.Text)
    remarks = db.Column(db.Text)

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'chapter_id': self.chapter_id,
            'order_number': self.order_number,
            'title': self.title,
            'description': self.description,
            'periods_required': self.periods_required,
            'periods_taken': self.periods_taken,
            'planned_date': self.planned_date.isoformat() if self.planned_date else None,
            'actual_date': self.actual_date.isoformat() if self.actual_date else None,
            'status': self.status,
            'teaching_method': self.teaching_method,
            'resources': self.resources,
            'homework_assigned': self.homework_assigned,
            'remarks': self.remarks
        })
        return data


class WeeklySyllabus(BaseModel):
    """Weekly syllabus plan entry for a teacher"""
    __tablename__ = 'weekly_syllabus'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)

    week_start_date = db.Column(db.Date, nullable=False)
    week_end_date = db.Column(db.Date, nullable=False)

    topics_planned = db.Column(db.Text, nullable=False)
    topics_covered = db.Column(db.Text)
    homework = db.Column(db.Text)
    assessment_notes = db.Column(db.Text)
    remarks = db.Column(db.Text)

    status = db.Column(db.String(20), default='planned')  # planned, in_progress, completed
    submitted_at = db.Column(db.DateTime, nullable=True)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    review_status = db.Column(db.String(20))  # pending, approved, revision_needed

    # Relationships
    teacher = db.relationship('User', foreign_keys=[teacher_id])
    class_obj = db.relationship('Class', foreign_keys=[class_id])
    section = db.relationship('Section', foreign_keys=[section_id])
    subject = db.relationship('Subject', foreign_keys=[subject_id])
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id])

    __table_args__ = (
        db.UniqueConstraint('school_id', 'teacher_id', 'class_id', 'subject_id',
                            'week_start_date', name='uq_weekly_syllabus'),
        db.Index('idx_weekly_teacher', 'school_id', 'teacher_id', 'week_start_date'),
    )

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.name if self.teacher else None,
            'class_id': self.class_id,
            'class_name': self.class_obj.name if self.class_obj else None,
            'section_id': self.section_id,
            'section_name': self.section.name if self.section else None,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else None,
            'week_start_date': self.week_start_date.isoformat(),
            'week_end_date': self.week_end_date.isoformat(),
            'topics_planned': self.topics_planned,
            'topics_covered': self.topics_covered,
            'homework': self.homework,
            'assessment_notes': self.assessment_notes,
            'remarks': self.remarks,
            'status': self.status,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'review_status': self.review_status
        })
        return data
