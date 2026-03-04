"""
Alert & Notification Models
Auto alerts for attendance, fees, exams, leaves
"""
from app.models.base import BaseModel
from app.extensions import db
from datetime import datetime


class AlertType:
    """Alert type constants"""
    LOW_ATTENDANCE = 'low_attendance'
    FEE_OVERDUE = 'fee_overdue'
    FEE_REMINDER = 'fee_reminder'
    EXAM_REMINDER = 'exam_reminder'
    STAFF_LEAVE = 'staff_leave'
    DOCUMENT_EXPIRY = 'document_expiry'
    VEHICLE_EXPIRY = 'vehicle_expiry'
    BOOK_OVERDUE = 'book_overdue'
    SUBSCRIPTION_EXPIRY = 'subscription_expiry'
    CUSTOM = 'custom'

    CHOICES = [
        LOW_ATTENDANCE, FEE_OVERDUE, FEE_REMINDER, EXAM_REMINDER,
        STAFF_LEAVE, DOCUMENT_EXPIRY, VEHICLE_EXPIRY, BOOK_OVERDUE,
        SUBSCRIPTION_EXPIRY, CUSTOM
    ]


class AlertPriority:
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'
    CHOICES = [LOW, MEDIUM, HIGH, CRITICAL]


class Alert(BaseModel):
    """Alert/Notification record - Multi-tenant"""
    __tablename__ = 'alerts'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default=AlertPriority.MEDIUM)

    # Targeting
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Specific user
    target_role = db.Column(db.String(50), nullable=True)  # e.g., 'Admin', 'Teacher', 'Parent'
    target_class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)

    # Related entity
    entity_type = db.Column(db.String(50), nullable=True)  # student, fee, exam, vehicle
    entity_id = db.Column(db.Integer, nullable=True)

    # Status
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime, nullable=True)
    is_dismissed = db.Column(db.Boolean, default=False)
    dismissed_at = db.Column(db.DateTime, nullable=True)

    # Delivery
    send_email = db.Column(db.Boolean, default=False)
    send_sms = db.Column(db.Boolean, default=False)
    send_push = db.Column(db.Boolean, default=True)
    email_sent = db.Column(db.Boolean, default=False)
    sms_sent = db.Column(db.Boolean, default=False)

    # Auto-generated or manual
    is_auto = db.Column(db.Boolean, default=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Expiry
    expires_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    target_user = db.relationship('User', foreign_keys=[target_user_id], backref='received_alerts')
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    __table_args__ = (
        db.Index('idx_alert_school_user', 'school_id', 'target_user_id'),
        db.Index('idx_alert_type', 'school_id', 'alert_type', 'is_read'),
    )

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'alert_type': self.alert_type,
            'title': self.title,
            'message': self.message,
            'priority': self.priority,
            'target_user_id': self.target_user_id,
            'target_role': self.target_role,
            'target_class_id': self.target_class_id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'is_dismissed': self.is_dismissed,
            'is_auto': self.is_auto,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        })
        return data


class AlertRule(BaseModel):
    """Alert automation rules - configurable per school"""
    __tablename__ = 'alert_rules'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    is_enabled = db.Column(db.Boolean, default=True)

    # Rule configuration (JSON)
    conditions = db.Column(db.JSON, default={})
    # e.g., {"threshold": 75, "period_days": 30} for low attendance
    # e.g., {"days_before_due": 7} for fee reminders

    # Notification channels
    notify_email = db.Column(db.Boolean, default=False)
    notify_sms = db.Column(db.Boolean, default=False)
    notify_push = db.Column(db.Boolean, default=True)

    # Target
    target_roles = db.Column(db.JSON, default=[])  # ["Admin", "Parent"]

    # Frequency
    frequency = db.Column(db.String(20), default='daily')  # immediate, daily, weekly

    # Relationships
    school = db.relationship('School', backref='alert_rules')

    __table_args__ = (
        db.UniqueConstraint('school_id', 'alert_type', 'name', name='uq_alert_rule'),
    )

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'alert_type': self.alert_type,
            'name': self.name,
            'description': self.description,
            'is_enabled': self.is_enabled,
            'conditions': self.conditions,
            'notify_email': self.notify_email,
            'notify_sms': self.notify_sms,
            'notify_push': self.notify_push,
            'target_roles': self.target_roles,
            'frequency': self.frequency
        })
        return data
