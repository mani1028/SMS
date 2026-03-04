"""
System Settings models: AcademicYear, SchoolConfiguration
Multi-tenant, inheriting from BaseModel
"""

from app.models.base import BaseModel
from app.extensions import db
from datetime import datetime


class AcademicYear(BaseModel):
    """Academic year management - Multi-tenant"""
    __tablename__ = 'academic_years'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    year = db.Column(db.String(20), nullable=False)  # e.g., "2024-2025"
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    is_current = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    
    __table_args__ = (db.UniqueConstraint('school_id', 'year', name='uq_school_academic_year'),)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'year': self.year,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'is_active': self.is_active,
            'is_current': self.is_current,
            'description': self.description
        })
        return data


class SchoolConfiguration(BaseModel):
    """School configuration and settings - Multi-tenant"""
    __tablename__ = 'school_configurations'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False, unique=True)
    
    # Academic Settings
    academic_year = db.Column(db.String(20), nullable=True)  # Current academic year
    class_start_time = db.Column(db.Time, nullable=True)
    class_end_time = db.Column(db.Time, nullable=True)
    lunch_break_start = db.Column(db.Time, nullable=True)
    lunch_break_end = db.Column(db.Time, nullable=True)
    school_days = db.Column(db.String(100), default='MTWTFS')  # Monday-Saturday
    
    # Fee Settings
    currency_symbol = db.Column(db.String(10), default='₹')
    tax_rate = db.Column(db.Float, default=18.0)  # GST percentage
    standard_fine_per_day = db.Column(db.Numeric(10, 2), default=10)
    
    # Attendance Settings
    attendance_marking_enabled = db.Column(db.Boolean, default=True)
    subject_wise_attendance = db.Column(db.Boolean, default=False)
    
    # Grading Settings
    grading_scale = db.Column(db.String(100), default='CBSE')  # Default grading system
    
    # Communication Settings
    email_notifications_enabled = db.Column(db.Boolean, default=True)
    sms_notifications_enabled = db.Column(db.Boolean, default=False)
    email_gateway_api_key = db.Column(db.String(255), nullable=True)
    sms_gateway_api_key = db.Column(db.String(255), nullable=True)
    
    # Branding & Theme
    school_name = db.Column(db.String(255), nullable=False)
    school_logo_url = db.Column(db.String(500), nullable=True)
    school_address = db.Column(db.Text, nullable=True)
    school_phone = db.Column(db.String(20), nullable=True)
    school_email = db.Column(db.String(100), nullable=True)
    school_website = db.Column(db.String(255), nullable=True)
    primary_color = db.Column(db.String(20), default='#003366')
    secondary_color = db.Column(db.String(20), default='#FF6600')
    
    # Transport Settings
    enable_transport = db.Column(db.Boolean, default=True)
    gps_tracking_enabled = db.Column(db.Boolean, default=False)
    
    # Hostel Settings
    enable_hostel = db.Column(db.Boolean, default=False)
    
    # Library Settings
    enable_library = db.Column(db.Boolean, default=True)
    book_issue_limit = db.Column(db.Integer, default=5)
    book_issue_days = db.Column(db.Integer, default=14)
    
    # Payment Gateway
    payment_gateway = db.Column(db.String(50), nullable=True)  # razorpay, paypal, etc.
    payment_gateway_key = db.Column(db.String(500), nullable=True)
    payment_gateway_secret = db.Column(db.String(500), nullable=True)
    
    # Security Settings
    session_timeout_minutes = db.Column(db.Integer, default=30)
    require_password_change_days = db.Column(db.Integer, default=90)
    
    # System Settings
    enable_demo_data = db.Column(db.Boolean, default=False)
    enable_backup = db.Column(db.Boolean, default=True)
    backup_frequency = db.Column(db.String(20), default='weekly')  # daily, weekly, monthly
    
    updated_on = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'academic_year': self.academic_year,
            'class_start_time': self.class_start_time.isoformat() if self.class_start_time else None,
            'class_end_time': self.class_end_time.isoformat() if self.class_end_time else None,
            'lunch_break_start': self.lunch_break_start.isoformat() if self.lunch_break_start else None,
            'lunch_break_end': self.lunch_break_end.isoformat() if self.lunch_break_end else None,
            'school_days': self.school_days,
            'currency_symbol': self.currency_symbol,
            'tax_rate': self.tax_rate,
            'standard_fine_per_day': float(self.standard_fine_per_day),
            'attendance_marking_enabled': self.attendance_marking_enabled,
            'subject_wise_attendance': self.subject_wise_attendance,
            'grading_scale': self.grading_scale,
            'email_notifications_enabled': self.email_notifications_enabled,
            'sms_notifications_enabled': self.sms_notifications_enabled,
            'school_name': self.school_name,
            'school_logo_url': self.school_logo_url,
            'school_address': self.school_address,
            'school_phone': self.school_phone,
            'school_email': self.school_email,
            'school_website': self.school_website,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'enable_transport': self.enable_transport,
            'gps_tracking_enabled': self.gps_tracking_enabled,
            'enable_hostel': self.enable_hostel,
            'enable_library': self.enable_library,
            'book_issue_limit': self.book_issue_limit,
            'book_issue_days': self.book_issue_days,
            'session_timeout_minutes': self.session_timeout_minutes,
            'require_password_change_days': self.require_password_change_days,
            'enable_demo_data': self.enable_demo_data,
            'enable_backup': self.enable_backup,
            'backup_frequency': self.backup_frequency,
            'updated_on': self.updated_on.isoformat()
        })
        return data


class AuditLog(BaseModel):
    """Audit log for tracking system changes - Multi-tenant"""
    __tablename__ = 'audit_logs'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)  # e.g., "CREATE_STUDENT", "UPDATE_FEE"
    entity_type = db.Column(db.String(100), nullable=False)  # e.g., "Student", "FeePayment"
    entity_id = db.Column(db.Integer, nullable=True)
    old_values = db.Column(db.Text, nullable=True)  # JSON string of old values
    new_values = db.Column(db.Text, nullable=True)  # JSON string of new values
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(50), nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='audit_logs')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'timestamp': self.timestamp.isoformat(),
            'ip_address': self.ip_address
        })
        return data


class SystemLog(BaseModel):
    """System-level logs - Multi-tenant"""
    __tablename__ = 'system_logs'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    log_level = db.Column(db.String(20), default='INFO')  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message = db.Column(db.Text)
    module = db.Column(db.String(100), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'log_level': self.log_level,
            'message': self.message,
            'module': self.module,
            'timestamp': self.timestamp.isoformat()
        })
        return data
