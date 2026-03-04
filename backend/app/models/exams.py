"""
Examination and Grading models
Multi-tenant, inheriting from BaseModel
"""

from app.models.base import BaseModel
from app.extensions import db
from datetime import datetime


class ExamTerm(BaseModel):
    """Exam term/semester - Multi-tenant"""
    __tablename__ = 'exam_terms'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Term 1", "Semester 1"
    academic_year = db.Column(db.String(20), nullable=False)  # e.g., "2024-2025"
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    declaration_date = db.Column(db.Date, nullable=True)  # When results are declared
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    exam_schedules = db.relationship('ExamSchedule', back_populates='exam_term', cascade='all, delete-orphan')
    grade_books = db.relationship('GradeBook', back_populates='exam_term', cascade='all, delete-orphan')
    
    __table_args__ = (db.UniqueConstraint('school_id', 'name', 'academic_year', name='uq_exam_term'),)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'name': self.name,
            'academic_year': self.academic_year,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'declaration_date': self.declaration_date.isoformat() if self.declaration_date else None,
            'is_active': self.is_active
        })
        return data


class ExamSchedule(BaseModel):
    """Exam schedule - Multi-tenant"""
    __tablename__ = 'exam_schedules'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    exam_term_id = db.Column(db.Integer, db.ForeignKey('exam_terms.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    exam_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    room_number = db.Column(db.String(50), nullable=True)
    max_marks = db.Column(db.Integer, default=100)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    exam_term = db.relationship('ExamTerm', foreign_keys=[exam_term_id], back_populates='exam_schedules')
    class_obj = db.relationship('Class', foreign_keys=[class_id])
    section = db.relationship('Section', foreign_keys=[section_id])
    subject = db.relationship('Subject', foreign_keys=[subject_id])
    grade_books = db.relationship('GradeBook', back_populates='exam_schedule', cascade='all, delete-orphan')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'exam_term_id': self.exam_term_id,
            'exam_term_name': self.exam_term.name,
            'class_id': self.class_id,
            'class_name': self.class_obj.name,
            'section_id': self.section_id,
            'section_name': self.section.name if self.section else None,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name,
            'exam_date': self.exam_date.isoformat(),
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'room_number': self.room_number,
            'max_marks': self.max_marks,
            'is_active': self.is_active
        })
        return data


class GradingScale(BaseModel):
    """Grading scale/scheme - Multi-tenant"""
    __tablename__ = 'grading_scales'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # e.g., "CBSE 9-Point"
    min_percentage = db.Column(db.Float, nullable=False)
    max_percentage = db.Column(db.Float, nullable=False)
    grade = db.Column(db.String(5), nullable=False)  # e.g., "A+", "A", "B"
    grade_point = db.Column(db.Float, nullable=False)  # For GPA calculation
    description = db.Column(db.Text)
    
    __table_args__ = (db.UniqueConstraint('school_id', 'name', 'grade', name='uq_grading_scale'),)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'name': self.name,
            'min_percentage': self.min_percentage,
            'max_percentage': self.max_percentage,
            'grade': self.grade,
            'grade_point': self.grade_point,
            'description': self.description
        })
        return data


class GradeBook(BaseModel):
    """Student marks/grades for exam - Multi-tenant"""
    __tablename__ = 'grade_books'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    exam_term_id = db.Column(db.Integer, db.ForeignKey('exam_terms.id'), nullable=False)
    exam_schedule_id = db.Column(db.Integer, db.ForeignKey('exam_schedules.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    obtained_marks = db.Column(db.Float, nullable=True)
    max_marks = db.Column(db.Integer, default=100)
    percentage = db.Column(db.Float, nullable=True)
    grade = db.Column(db.String(5), nullable=True)
    remarks = db.Column(db.Text)
    
    # Relationships
    exam_term = db.relationship('ExamTerm', foreign_keys=[exam_term_id], back_populates='grade_books')
    exam_schedule = db.relationship('ExamSchedule', foreign_keys=[exam_schedule_id], back_populates='grade_books')
    student = db.relationship('User', foreign_keys=[student_id], backref='grade_books')
    subject = db.relationship('Subject', foreign_keys=[subject_id], back_populates='grade_books')
    
    __table_args__ = (db.UniqueConstraint('school_id', 'exam_schedule_id', 'student_id', 'subject_id', 
                                          name='uq_grad_entry'),)
    
    def calculate_percentage(self):
        """Auto-calculate percentage"""
        if self.obtained_marks is not None and self.max_marks:
            self.percentage = round((self.obtained_marks / self.max_marks) * 100, 2)
    
    def determine_grade(self):
        """Determine grade based on percentage and grading scale"""
        if self.percentage is not None:
            # Get school's grading scale - you can make this configurable
            grading_scale = GradingScale.query.filter(
                GradingScale.school_id == self.school_id,
                GradingScale.min_percentage <= self.percentage,
                GradingScale.max_percentage >= self.percentage
            ).first()
            
            if grading_scale:
                self.grade = grading_scale.grade
    
    def to_dict(self):
        self.calculate_percentage()
        self.determine_grade()
        
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'exam_term_id': self.exam_term_id,
            'exam_term_name': self.exam_term.name if self.exam_term else None,
            'exam_schedule_id': self.exam_schedule_id,
            'student_id': self.student_id,
            'student_name': self.student.name,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name,
            'obtained_marks': self.obtained_marks,
            'max_marks': self.max_marks,
            'percentage': self.percentage,
            'grade': self.grade,
            'remarks': self.remarks
        })
        return data


class StudentRank(BaseModel):
    """Student rankings by class/section for each term - Multi-tenant"""
    __tablename__ = 'student_ranks'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    exam_term_id = db.Column(db.Integer, db.ForeignKey('exam_terms.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rank = db.Column(db.Integer, nullable=False)
    total_percentage = db.Column(db.Float, nullable=False)
    gpa = db.Column(db.Float, nullable=True)
    total_students = db.Column(db.Integer, nullable=False)
    
    # Relationships
    exam_term = db.relationship('ExamTerm', foreign_keys=[exam_term_id])
    class_obj = db.relationship('Class', foreign_keys=[class_id])
    section = db.relationship('Section', foreign_keys=[section_id])
    student = db.relationship('User', foreign_keys=[student_id], backref='student_ranks')
    
    __table_args__ = (db.UniqueConstraint('school_id', 'exam_term_id', 'class_id', 'section_id', 'student_id', 
                                          name='uq_student_rank'),)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'exam_term_id': self.exam_term_id,
            'exam_term_name': self.exam_term.name,
            'class_id': self.class_id,
            'class_name': self.class_obj.name,
            'section_id': self.section_id,
            'section_name': self.section.name if self.section else None,
            'student_id': self.student_id,
            'student_name': self.student.name,
            'rank': self.rank,
            'total_percentage': self.total_percentage,
            'gpa': self.gpa,
            'total_students': self.total_students
        })
        return data
