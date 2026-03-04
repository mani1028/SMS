"""
Attendance and Leave models
Multi-tenant, inheriting from BaseModel
"""

from app.models.base import BaseModel
from app.extensions import db
from datetime import datetime
from sqlalchemy import func, and_


class AttendanceStatus:
    """Attendance status constants"""
    PRESENT = 'present'
    ABSENT = 'absent'
    LATE = 'late'
    HALF_DAY = 'half_day'
    EXCUSED = 'excused'
    
    CHOICES = [PRESENT, ABSENT, LATE, HALF_DAY, EXCUSED]


class Attendance(BaseModel):
    """Student/Staff attendance record - Multi-tenant"""
    __tablename__ = 'attendance'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True)  # For students
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=True)  # Subject-wise tracking (optional)
    attendance_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default=AttendanceStatus.ABSENT)  # present, absent, late, half_day, excused
    remarks = db.Column(db.Text)
    marked_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='attendance_records')
    marked_by = db.relationship('User', foreign_keys=[marked_by_id], backref='marked_attendance')
    section = db.relationship('Section', foreign_keys=[section_id])
    subject = db.relationship('Subject', foreign_keys=[subject_id])
    
    __table_args__ = (db.UniqueConstraint('school_id', 'user_id', 'section_id', 'subject_id', 
                                          'attendance_date', name='uq_attendance'),)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'user_id': self.user_id,
            'user_name': self.user.name,
            'section_id': self.section_id,
            'section_name': self.section.name if self.section else None,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else None,
            'attendance_date': self.attendance_date.isoformat(),
            'status': self.status,
            'remarks': self.remarks,
            'marked_by_id': self.marked_by_id,
            'marked_by_name': self.marked_by.name
        })
        return data


class LeaveType:
    """Leave type constants"""
    CASUAL = 'casual'
    MEDICAL = 'medical'
    EARNED = 'earned'
    MATERNITY = 'maternity'
    PATERNITY = 'paternity'
    STUDY = 'study'
    OTHER = 'other'
    
    CHOICES = [CASUAL, MEDICAL, EARNED, MATERNITY, PATERNITY, STUDY, OTHER]


class LeaveStatus:
    """Leave request status constants"""
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    CANCELLED = 'cancelled'
    
    CHOICES = [PENDING, APPROVED, REJECTED, CANCELLED]


class LeaveRequest(BaseModel):
    """Leave request for students/staff - Multi-tenant"""
    __tablename__ = 'leave_requests'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    leave_type = db.Column(db.String(20), nullable=False)  # casual, medical, earned, etc.
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    number_of_days = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default=LeaveStatus.PENDING)  # pending, approved, rejected, cancelled
    supporting_doc_url = db.Column(db.String(500), nullable=True)
    
    # Approval workflow
    requested_on = db.Column(db.DateTime, default=datetime.utcnow)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_on = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='leave_requests')
    approved_by = db.relationship('User', foreign_keys=[approved_by_id], backref='approved_leaves')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'user_id': self.user_id,
            'user_name': self.user.name,
            'leave_type': self.leave_type,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'number_of_days': self.number_of_days,
            'reason': self.reason,
            'status': self.status,
            'supporting_doc_url': self.supporting_doc_url,
            'requested_on': self.requested_on.isoformat(),
            'approved_by_id': self.approved_by_id,
            'approved_by_name': self.approved_by.name if self.approved_by else None,
            'approved_on': self.approved_on.isoformat() if self.approved_on else None,
            'rejection_reason': self.rejection_reason
        })
        return data


class StaffCheckInOut(BaseModel):
    """Staff check-in/check-out tracking - Multi-tenant"""
    __tablename__ = 'staff_check_in_out'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    check_in_time = db.Column(db.DateTime, nullable=False)
    check_out_time = db.Column(db.DateTime, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    device_info = db.Column(db.Text, nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='check_in_outs')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'user_id': self.user_id,
            'user_name': self.user.name,
            'check_in_time': self.check_in_time.isoformat(),
            'check_out_time': self.check_out_time.isoformat() if self.check_out_time else None,
            'location': self.location,
            'device_info': self.device_info
        })
        return data
