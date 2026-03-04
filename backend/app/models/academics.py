"""
Academic models: Class, Section, Subject, Timetable, ClassTeacherAssignment
Multi-tenant, inheriting from BaseModel
"""

from app.models.base import BaseModel
from app.extensions import db
from datetime import datetime


class Subject(BaseModel):
    """Subject model - Multi-tenant"""
    __tablename__ = 'subjects'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    timetable_slots = db.relationship('TimetableSlot', foreign_keys='TimetableSlot.subject_id', back_populates='subject', cascade='all, delete-orphan')
    grade_books = db.relationship('GradeBook', back_populates='subject', cascade='all, delete-orphan')
    
    __table_args__ = (db.UniqueConstraint('school_id', 'code', name='uq_school_subject_code'),)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'is_active': self.is_active
        })
        return data


class Class(BaseModel):
    """Class/Grade model - Multi-tenant"""
    __tablename__ = 'classes'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)  # e.g., "Class 10", "Grade 12"
    numeric_class = db.Column(db.Integer, nullable=False)  # e.g., 10, 12
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    sections = db.relationship('Section', backref='class_obj', cascade='all, delete-orphan')
    class_teacher_assignments = db.relationship('ClassTeacherAssignment', back_populates='class_obj', cascade='all, delete-orphan')
    
    __table_args__ = (db.UniqueConstraint('school_id', 'name', name='uq_school_class'),)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'name': self.name,
            'numeric_class': self.numeric_class,
            'description': self.description,
            'is_active': self.is_active,
            'sections': [s.to_dict() for s in self.sections]
        })
        return data


class Section(BaseModel):
    """Section model - Multi-tenant (e.g., A, B, C within Class 10)"""
    __tablename__ = 'sections'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)  # e.g., "A", "B", "C"
    capacity = db.Column(db.Integer, default=50)
    class_teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    class_teacher = db.relationship('User', foreign_keys=[class_teacher_id])
    timetable_slots = db.relationship('TimetableSlot', backref='section_obj', cascade='all, delete-orphan')
    attendance_records = db.relationship('Attendance', backref='section_obj', cascade='all, delete-orphan')
    
    __table_args__ = (db.UniqueConstraint('school_id', 'class_id', 'name', name='uq_school_section'),)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'class_id': self.class_id,
            'name': self.name,
            'capacity': self.capacity,
            'class_teacher_id': self.class_teacher_id,
            'class_teacher_name': self.class_teacher.name if self.class_teacher else None,
            'is_active': self.is_active
        })
        return data


class ClassTeacherAssignment(BaseModel):
    """Assign teachers to classes for subject teaching"""
    __tablename__ = 'class_teacher_assignments'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True)  # Optional per-section assignment
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    class_obj = db.relationship('Class', back_populates='class_teacher_assignments')
    section = db.relationship('Section', foreign_keys=[section_id])
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='class_assignments')
    subject = db.relationship('Subject', backref='teacher_assignments')
    
    __table_args__ = (
        db.UniqueConstraint('school_id', 'class_id', 'section_id', 'teacher_id', 'subject_id', 
                           name='uq_class_teacher_subject'),
    )
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'class_id': self.class_id,
            'section_id': self.section_id,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.name,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name,
            'is_active': self.is_active
        })
        return data


class TimetableSlot(BaseModel):
    """Timetable slot - Maps teacher, class/section, subject, day, and time"""
    __tablename__ = 'timetable_slots'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    day_of_week = db.Column(db.String(20), nullable=False)  # Monday, Tuesday, etc.
    start_time = db.Column(db.Time, nullable=False)  # HH:MM
    end_time = db.Column(db.Time, nullable=False)  # HH:MM
    room_number = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    class_obj = db.relationship('Class', foreign_keys=[class_id])
    section = db.relationship('Section', foreign_keys=[section_id])
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='timetable_slots')
    subject = db.relationship('Subject', foreign_keys=[subject_id], back_populates='timetable_slots')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'class_id': self.class_id,
            'class_name': self.class_obj.name,
            'section_id': self.section_id,
            'section_name': self.section.name,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.name,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'room_number': self.room_number,
            'is_active': self.is_active
        })
        return data
    
    @staticmethod
    def check_conflict(school_id, teacher_id, day_of_week, start_time, end_time, exclude_slot_id=None):
        """
        Check for timetable conflicts:
        - Same teacher cannot teach two classes at overlapping times
        - Same room cannot be used at overlapping times (if room tracking is needed)
        """
        query = TimetableSlot.query.filter(
            TimetableSlot.school_id == school_id,
            TimetableSlot.teacher_id == teacher_id,
            TimetableSlot.day_of_week == day_of_week,
            TimetableSlot.is_active == True
        )
        
        if exclude_slot_id:
            query = query.filter(TimetableSlot.id != exclude_slot_id)
        
        for slot in query.all():
            # Check for time overlap
            if not (end_time <= slot.start_time or start_time >= slot.end_time):
                return True  # Conflict found
        
        return False  # No conflict
