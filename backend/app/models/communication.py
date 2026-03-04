"""
Communication and Documents models
Multi-tenant, inheriting from BaseModel
"""

from app.models.base import BaseModel
from app.extensions import db
from datetime import datetime


class NoticeType:
    """Notice type constants"""
    GENERAL = 'general'
    ACADEMIC = 'academic'
    ADMINISTRATIVE = 'administrative'
    URGENT = 'urgent'
    CIRCULAR = 'circular'
    
    CHOICES = [GENERAL, ACADEMIC, ADMINISTRATIVE, URGENT, CIRCULAR]


class Notice(BaseModel):
    """School notices - Multi-tenant"""
    __tablename__ = 'notices'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    notice_type = db.Column(db.String(50), default=NoticeType.GENERAL)
    published_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    published_date = db.Column(db.DateTime, default=datetime.utcnow)
    visibility = db.Column(db.String(50), default='all')  # all, staff_only, students, specific_class, etc.
    target_class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)  # If visibility is specific_class
    is_active = db.Column(db.Boolean, default=True)
    attachment_url = db.Column(db.String(500), nullable=True)
    
    # Relationships
    published_by = db.relationship('User', foreign_keys=[published_by_id], backref='published_notices')
    target_class = db.relationship('Class', foreign_keys=[target_class_id])
    views = db.relationship('NoticeView', back_populates='notice', cascade='all, delete-orphan')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'title': self.title,
            'content': self.content,
            'notice_type': self.notice_type,
            'published_by_id': self.published_by_id,
            'published_by_name': self.published_by.name,
            'published_date': self.published_date.isoformat(),
            'visibility': self.visibility,
            'target_class_id': self.target_class_id,
            'target_class_name': self.target_class.name if self.target_class else None,
            'is_active': self.is_active,
            'attachment_url': self.attachment_url,
            'view_count': len(self.views)
        })
        return data


class NoticeView(BaseModel):
    """Track notice views - Multi-tenant"""
    __tablename__ = 'notice_views'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    notice_id = db.Column(db.Integer, db.ForeignKey('notices.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    notice = db.relationship('Notice', foreign_keys=[notice_id], back_populates='views')
    user = db.relationship('User', foreign_keys=[user_id])


class Event(BaseModel):
    """School events/calendar - Multi-tenant"""
    __tablename__ = 'events'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    event_type = db.Column(db.String(50), nullable=False)  # holiday, exam, sports, cultural, etc.
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=True)
    attachment_url = db.Column(db.String(500), nullable=True)
    
    # Relationships
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_events')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'title': self.title,
            'description': self.description,
            'event_date': self.event_date.isoformat(),
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'location': self.location,
            'event_type': self.event_type,
            'created_by_id': self.created_by_id,
            'created_by_name': self.created_by.name,
            'is_public': self.is_public,
            'attachment_url': self.attachment_url
        })
        return data


class Homework(BaseModel):
    """Homework assignment - Multi-tenant"""
    __tablename__ = 'homework'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    assignment_date = db.Column(db.Date, default=lambda: datetime.utcnow().date())
    due_date = db.Column(db.Date, nullable=False)
    attachment_url = db.Column(db.String(500), nullable=True)
    marks = db.Column(db.Integer, nullable=True)
    
    # Relationships
    class_obj = db.relationship('Class', foreign_keys=[class_id])
    section = db.relationship('Section', foreign_keys=[section_id])
    subject = db.relationship('Subject', foreign_keys=[subject_id])
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='homework_assignments')
    submissions = db.relationship('HomeworkSubmission', back_populates='homework', cascade='all, delete-orphan')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'class_id': self.class_id,
            'class_name': self.class_obj.name,
            'section_id': self.section_id,
            'section_name': self.section.name if self.section else None,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.name,
            'title': self.title,
            'description': self.description,
            'assignment_date': self.assignment_date.isoformat(),
            'due_date': self.due_date.isoformat(),
            'attachment_url': self.attachment_url,
            'marks': self.marks,
            'submission_count': len(self.submissions)
        })
        return data


class HomeworkSubmission(BaseModel):
    """Homework submission by student - Multi-tenant"""
    __tablename__ = 'homework_submissions'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    homework_id = db.Column(db.Integer, db.ForeignKey('homework.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    file_url = db.Column(db.String(500), nullable=True)
    is_late = db.Column(db.Boolean, default=False)
    marks_obtained = db.Column(db.Integer, nullable=True)
    feedback = db.Column(db.Text)
    is_evaluated = db.Column(db.Boolean, default=False)
    evaluated_on = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    homework = db.relationship('Homework', foreign_keys=[homework_id], back_populates='submissions')
    student = db.relationship('User', foreign_keys=[student_id], backref='homework_submissions')
    
    __table_args__ = (db.UniqueConstraint('school_id', 'homework_id', 'student_id', name='uq_homework_submission'),)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'homework_id': self.homework_id,
            'homework_title': self.homework.title,
            'student_id': self.student_id,
            'student_name': self.student.name,
            'submission_date': self.submission_date.isoformat(),
            'file_url': self.file_url,
            'is_late': self.is_late,
            'marks_obtained': self.marks_obtained,
            'feedback': self.feedback,
            'is_evaluated': self.is_evaluated,
            'evaluated_on': self.evaluated_on.isoformat() if self.evaluated_on else None
        })
        return data


class Announcement(BaseModel):
    """General announcements - Multi-tenant"""
    __tablename__ = 'announcements'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    announced_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    announcement_date = db.Column(db.DateTime, default=datetime.utcnow)
    expire_date = db.Column(db.DateTime, nullable=True)
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    
    # Relationships
    announced_by = db.relationship('User', foreign_keys=[announced_by_id], backref='announcements')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'title': self.title,
            'content': self.content,
            'announced_by_id': self.announced_by_id,
            'announced_by_name': self.announced_by.name,
            'announcement_date': self.announcement_date.isoformat(),
            'expire_date': self.expire_date.isoformat() if self.expire_date else None,
            'priority': self.priority
        })
        return data


class Document(BaseModel):
    """Document management - Multi-tenant"""
    __tablename__ = 'documents'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # admission_form, certificate, report, etc.
    file_url = db.Column(db.String(500), nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_date = db.Column(db.DateTime, default=datetime.utcnow)
    related_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # If specific to a user
    is_public = db.Column(db.Boolean, default=False)
    
    # Relationships
    uploaded_by = db.relationship('User', foreign_keys=[uploaded_by_id], backref='uploaded_documents')
    related_user = db.relationship('User', foreign_keys=[related_user_id])
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'title': self.title,
            'document_type': self.document_type,
            'file_url': self.file_url,
            'uploaded_by_id': self.uploaded_by_id,
            'uploaded_by_name': self.uploaded_by.name,
            'uploaded_date': self.uploaded_date.isoformat(),
            'related_user_id': self.related_user_id,
            'related_user_name': self.related_user.name if self.related_user else None,
            'is_public': self.is_public
        })
        return data
