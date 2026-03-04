"""
Subscription and Billing Models for SaaS Platform
"""
from app.models.base import BaseModel
from app.extensions import db
from datetime import datetime, timedelta
import json


class Plan(BaseModel):
    """Subscription plans available on the platform"""
    __tablename__ = 'plans'
    
    name = db.Column(db.String(100), nullable=False, unique=True)  # Free, Basic, Pro, Enterprise
    description = db.Column(db.Text)
    price_monthly = db.Column(db.Float, default=0)  # 0 for free plan
    price_annual = db.Column(db.Float, default=0)
    
    # Feature limits (JSON for flexibility)
    features = db.Column(db.JSON, default={})  # {"students": 100, "teachers": 20, "sms_credits": 1000}
    max_students = db.Column(db.Integer, default=999999)  # Unlimited for free
    max_teachers = db.Column(db.Integer, default=999999)
    max_staff = db.Column(db.Integer, default=999999)
    storage_gb = db.Column(db.Integer, default=50)  # Cloud storage in GB
    sms_credits_monthly = db.Column(db.Integer, default=0)
    api_calls_per_day = db.Column(db.Integer, default=10000)
    
    # Feature access (JSON of feature flags)
    enabled_features = db.Column(db.JSON, default={})  
    # {"crm": true, "library": true, "transport": true, "advanced_analytics": false}
    
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    
    # Relationships
    subscriptions = db.relationship('Subscription', backref='plan', cascade='all, delete-orphan')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'name': self.name,
            'description': self.description,
            'price_monthly': self.price_monthly,
            'price_annual': self.price_annual,
            'max_students': self.max_students,
            'max_teachers': self.max_teachers,
            'storage_gb': self.storage_gb,
            'sms_credits_monthly': self.sms_credits_monthly,
            'api_calls_per_day': self.api_calls_per_day,
            'features': self.features,
            'enabled_features': self.enabled_features,
            'is_active': self.is_active
        })
        return data
    
    def __repr__(self):
        return f'<Plan {self.name}>'


class Subscription(BaseModel):
    """Active subscription for each school"""
    __tablename__ = 'subscriptions'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False, unique=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=False)
    
    # Status: active, cancelled, expired, trial, suspended
    status = db.Column(db.String(50), default='trial')
    
    # Trial info
    is_trial = db.Column(db.Boolean, default=True)
    trial_start_date = db.Column(db.DateTime, default=datetime.utcnow)
    trial_end_date = db.Column(db.DateTime)  # 14 days from trial_start_date
    
    # Subscription dates
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    renewal_date = db.Column(db.DateTime)
    
    # Billing cycle
    billing_cycle = db.Column(db.String(20), default='monthly')  # monthly or annual
    
    # Payment info
    auto_renew = db.Column(db.Boolean, default=True)
    payment_method = db.Column(db.String(50))  # stripe, razorpay, manual
    stripe_customer_id = db.Column(db.String(255))
    razorpay_customer_id = db.Column(db.String(255))
    
    # Relationships
    school = db.relationship('School', backref='subscription')
    billings = db.relationship('Billing', backref='subscription', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('school_id', name='uq_school_subscription'),
        db.Index('idx_subscription_status', 'status', 'renewal_date')
    )
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'plan': self.plan.to_dict(),
            'status': self.status,
            'is_trial': self.is_trial,
            'trial_start_date': self.trial_start_date.isoformat() if self.trial_start_date else None,
            'trial_end_date': self.trial_end_date.isoformat() if self.trial_end_date else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'renewal_date': self.renewal_date.isoformat() if self.renewal_date else None,
            'billing_cycle': self.billing_cycle,
            'auto_renew': self.auto_renew
        })
        return data
    
    def is_active(self):
        """Check if subscription is active"""
        if self.status == 'active':
            return True
        if self.status == 'trial' and self.trial_end_date and self.trial_end_date > datetime.utcnow():
            return True
        return False
    
    def days_until_renewal(self):
        """Days remaining until renewal"""
        if self.renewal_date:
            delta = self.renewal_date - datetime.utcnow()
            return max(0, delta.days)
        return None
    
    def __repr__(self):
        return f'<Subscription school_id={self.school_id} status={self.status}>'


class Billing(BaseModel):
    """Billing history and invoices"""
    __tablename__ = 'billings'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False)
    
    # Invoice details
    invoice_number = db.Column(db.String(50), nullable=False, unique=True)
    invoice_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    
    # Amount
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='INR')  # USD, INR, etc.
    
    # Payment status: pending, paid, failed, refunded, cancelled
    payment_status = db.Column(db.String(50), default='pending')
    
    # Payment info
    payment_method = db.Column(db.String(50))  # stripe, razorpay, manual, bank_transfer
    transaction_id = db.Column(db.String(255))  # Payment gateway transaction ID
    payment_date = db.Column(db.DateTime)

    # Retry count for failed payments
    retry_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Refund info
    refund_amount = db.Column(db.Float, default=0)
    refund_date = db.Column(db.DateTime)
    refund_reason = db.Column(db.Text)
    
    # Description
    description = db.Column(db.Text)
    
    # Relationships
    school = db.relationship('School', backref='billings')
    
    __table_args__ = (
        db.Index('idx_billing_school_date', 'school_id', 'invoice_date'),
        db.Index('idx_billing_status', 'payment_status', 'due_date')
    )
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'invoice_number': self.invoice_number,
            'invoice_date': self.invoice_date.isoformat(),
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'amount': self.amount,
            'currency': self.currency,
            'payment_status': self.payment_status,
            'payment_method': self.payment_method,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'refund_amount': self.refund_amount,
            'description': self.description
        })
        return data
    
    def __repr__(self):
        return f'<Billing {self.invoice_number}>'


class SchoolUsage(BaseModel):
    """Track usage metrics per school"""
    __tablename__ = 'school_usage'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False, unique=True)
    
    # Student & Staff counts
    students_count = db.Column(db.Integer, default=0)
    staff_count = db.Column(db.Integer, default=0)
    teachers_count = db.Column(db.Integer, default=0)
    
    # Storage
    storage_used_gb = db.Column(db.Float, default=0)
    
    # SMS & API
    sms_sent_this_month = db.Column(db.Integer, default=0)
    api_calls_today = db.Column(db.Integer, default=0)
    
    # Timestamps
    last_student_added = db.Column(db.DateTime)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    school = db.relationship('School', backref='usage')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'students_count': self.students_count,
            'staff_count': self.staff_count,
            'teachers_count': self.teachers_count,
            'storage_used_gb': self.storage_used_gb,
            'sms_sent_this_month': self.sms_sent_this_month,
            'api_calls_today': self.api_calls_today
        })
        return data
    
    def __repr__(self):
        return f'<SchoolUsage school_id={self.school_id}>'
