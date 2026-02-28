from app.models.base import BaseModel
from app.extensions import db
import enum


class AttendanceStatus(enum.Enum):
    """Staff attendance status."""
    PRESENT = 'Present'
    ABSENT = 'Absent'
    LEAVE = 'Leave'
    LATE = 'Late'


class LeaveStatus(enum.Enum):
    """Leave request status."""
    PENDING = 'Pending'
    APPROVED = 'Approved'
    REJECTED = 'Rejected'


class Staff(BaseModel):
    """Staff model for teaching and non-teaching staff."""
    __tablename__ = 'staff'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    staff_no = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100), nullable=False)
    date_of_joining = db.Column(db.Date, nullable=False)
    qualification = db.Column(db.String(255))
    experience = db.Column(db.Float, default=0.0)
    is_teaching_staff = db.Column(db.Boolean, default=True, nullable=False)

    salary = db.relationship(
        'StaffSalary',
        backref='staff',
        uselist=False,
        cascade='all, delete-orphan'
    )
    attendance_records = db.relationship(
        'StaffAttendance',
        backref='staff',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    leave_requests = db.relationship(
        'LeaveRequest',
        backref='staff',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    __table_args__ = (
        db.UniqueConstraint('school_id', 'staff_no', name='uq_school_staff_no'),
    )

    def to_dict(self, include_relations=False):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'user_id': self.user_id,
            'staff_no': self.staff_no,
            'department': self.department,
            'designation': self.designation,
            'date_of_joining': (
                self.date_of_joining.isoformat()
                if self.date_of_joining else None
            ),
            'qualification': self.qualification,
            'experience': self.experience,
            'is_teaching_staff': self.is_teaching_staff,
            'user': self.user.to_dict() if self.user else None,
            'salary': self.salary.to_dict() if self.salary else None,
        })

        if include_relations:
            data['attendance_records'] = [
                record.to_dict() for record in self.attendance_records.all()
            ]
            data['leave_requests'] = [
                leave.to_dict() for leave in self.leave_requests.all()
            ]

        return data


class StaffSalary(BaseModel):
    """Salary metadata for a staff member."""
    __tablename__ = 'staff_salaries'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    basic_salary = db.Column(db.Float, nullable=False, default=0.0)
    allowances = db.Column(db.Float, nullable=False, default=0.0)
    deductions = db.Column(db.Float, nullable=False, default=0.0)
    bank_account_details = db.Column(db.Text)
    pan_number = db.Column(db.String(50))

    __table_args__ = (
        db.UniqueConstraint('staff_id', name='uq_staff_salary_staff_id'),
    )

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'staff_id': self.staff_id,
            'basic_salary': self.basic_salary,
            'allowances': self.allowances,
            'deductions': self.deductions,
            'bank_account_details': self.bank_account_details,
            'pan_number': self.pan_number,
        })
        return data


class StaffAttendance(BaseModel):
    """Attendance entries for staff."""
    __tablename__ = 'staff_attendance'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum(AttendanceStatus), nullable=False)
    check_in_out_time = db.Column(db.String(255))

    __table_args__ = (
        db.UniqueConstraint('staff_id', 'date', name='uq_staff_attendance_date'),
    )

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'staff_id': self.staff_id,
            'date': self.date.isoformat() if self.date else None,
            'status': self.status.value if self.status else None,
            'check_in_out_time': self.check_in_out_time,
        })
        return data


class LeaveRequest(BaseModel):
    """Leave request for a staff member."""
    __tablename__ = 'leave_requests'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum(LeaveStatus), default=LeaveStatus.PENDING, nullable=False)

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'staff_id': self.staff_id,
            'leave_type': self.leave_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'reason': self.reason,
            'status': self.status.value if self.status else None,
        })
        return data
