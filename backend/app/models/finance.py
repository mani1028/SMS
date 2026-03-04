"""
Finance and Fee Management models
Multi-tenant, inheriting from BaseModel
"""

from app.models.base import BaseModel
from app.extensions import db
from datetime import datetime
from decimal import Decimal


class FeeType:
    """Fee type constants"""
    TUITION = 'tuition'
    TRANSPORT = 'transport'
    EXAM = 'exam'
    LIBRARY = 'library'
    ACTIVITY = 'activity'
    SPORTS = 'sports'
    UNIFORM = 'uniform'
    ADMISSION = 'admission'
    OTHER = 'other'
    
    CHOICES = [TUITION, TRANSPORT, EXAM, LIBRARY, ACTIVITY, SPORTS, UNIFORM, ADMISSION, OTHER]


class FeeStructure(BaseModel):
    """Fee structure template - Multi-tenant"""
    __tablename__ = 'fee_structures'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Class 10 Standard"
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)  # Optional, can be null for common structure
    academic_year = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text)
    
    # Relationships
    class_obj = db.relationship('Class', foreign_keys=[class_id])
    fee_components = db.relationship('FeeComponent', backref='fee_structure', cascade='all, delete-orphan')
    fee_plans = db.relationship('FeePlan', backref='fee_structure', cascade='all, delete-orphan')
    
    __table_args__ = (db.UniqueConstraint('school_id', 'name', 'academic_year', name='uq_fee_structure'),)
    
    def get_total_amount(self):
        """Calculate total fee amount from components"""
        return sum(component.amount for component in self.fee_components)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'name': self.name,
            'class_id': self.class_id,
            'class_name': self.class_obj.name if self.class_obj else None,
            'academic_year': self.academic_year,
            'is_active': self.is_active,
            'description': self.description,
            'total_amount': self.get_total_amount(),
            'fee_components': [fc.to_dict() for fc in self.fee_components]
        })
        return data


class FeeComponent(BaseModel):
    """Fee component (e.g., tuition, transport) - Multi-tenant"""
    __tablename__ = 'fee_components'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    fee_structure_id = db.Column(db.Integer, db.ForeignKey('fee_structures.id'), nullable=False)
    fee_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'fee_structure_id': self.fee_structure_id,
            'fee_type': self.fee_type,
            'description': self.description,
            'amount': float(self.amount)
        })
        return data


class FeePlanType:
    """Fee payment plan constants"""
    FULL = 'full'  # Full payment upfront
    INSTALLMENT = 'installment'  # Multiple installments
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    SEMESTER = 'semester'
    
    CHOICES = [FULL, INSTALLMENT, MONTHLY, QUARTERLY, SEMESTER]


class FeePlan(BaseModel):
    """Fee instalment plan - Multi-tenant"""
    __tablename__ = 'fee_plans'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    fee_structure_id = db.Column(db.Integer, db.ForeignKey('fee_structures.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Quarterly Plan"
    plan_type = db.Column(db.String(50), nullable=False)  # full, installment, monthly, etc.
    number_of_installments = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    installments = db.relationship('StudentFeeInstallment', back_populates='fee_plan', cascade='all, delete-orphan')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'fee_structure_id': self.fee_structure_id,
            'name': self.name,
            'plan_type': self.plan_type,
            'number_of_installments': self.number_of_installments,
            'is_active': self.is_active
        })
        return data


class StudentFeeInstallment(BaseModel):
    """Student fee installment - Multi-tenant"""
    __tablename__ = 'student_fee_installments'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    fee_plan_id = db.Column(db.Integer, db.ForeignKey('fee_plans.id'), nullable=False)
    installment_number = db.Column(db.Integer, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    paid_amount = db.Column(db.Numeric(10, 2), default=0)
    is_paid = db.Column(db.Boolean, default=False)
    paid_on = db.Column(db.Date, nullable=True)
    fine_charged = db.Column(db.Numeric(10, 2), default=0)
    
    # Relationships
    student = db.relationship('User', foreign_keys=[student_id], backref='fee_installments')
    fee_plan = db.relationship('FeePlan', foreign_keys=[fee_plan_id], back_populates='installments')
    payments = db.relationship('FeePayment', back_populates='installment', cascade='all, delete-orphan')
    
    __table_args__ = (db.UniqueConstraint('school_id', 'student_id', 'fee_plan_id', 'installment_number', 
                                          name='uq_student_installment'),)
    
    def calculate_outstanding(self):
        """Calculate outstanding amount"""
        return float(self.amount) - float(self.paid_amount)
    
    def is_overdue(self):
        """Check if installment is overdue"""
        from datetime import date
        return not self.is_paid and date.today() > self.due_date
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'student_id': self.student_id,
            'student_name': self.student.name,
            'fee_plan_id': self.fee_plan_id,
            'installment_number': self.installment_number,
            'due_date': self.due_date.isoformat(),
            'amount': float(self.amount),
            'paid_amount': float(self.paid_amount),
            'is_paid': self.is_paid,
            'paid_on': self.paid_on.isoformat() if self.paid_on else None,
            'fine_charged': float(self.fine_charged),
            'outstanding': self.calculate_outstanding(),
            'is_overdue': self.is_overdue()
        })
        return data


class PaymentStatus:
    """Payment status constants"""
    PENDING = 'pending'
    SUCCESS = 'success'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    REFUNDED = 'refunded'
    
    CHOICES = [PENDING, SUCCESS, FAILED, CANCELLED, REFUNDED]


class PaymentMethod:
    """Payment method constants"""
    CASH = 'cash'
    CHEQUE = 'cheque'
    UPI = 'upi'
    CARD = 'card'
    NET_BANKING = 'net_banking'
    WALLET = 'wallet'
    
    CHOICES = [CASH, CHEQUE, UPI, CARD, NET_BANKING, WALLET]


class FeePayment(BaseModel):
    """Fee payment record - Multi-tenant"""
    __tablename__ = 'fee_payments'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    installment_id = db.Column(db.Integer, db.ForeignKey('student_fee_installments.id'), nullable=True)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # cash, cheque, upi, card, etc.
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default=PaymentStatus.PENDING)
    receipt_number = db.Column(db.String(50), nullable=True)
    remarks = db.Column(db.Text)
    
    # Gateway-specific fields
    gateway_transaction_id = db.Column(db.String(255), nullable=True)
    gateway_response = db.Column(db.Text, nullable=True)
    
    # Relationships
    student = db.relationship('User', foreign_keys=[student_id], backref='fee_payments')
    installment = db.relationship('StudentFeeInstallment', foreign_keys=[installment_id], back_populates='payments')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'student_id': self.student_id,
            'student_name': self.student.name,
            'installment_id': self.installment_id,
            'transaction_id': self.transaction_id,
            'amount': float(self.amount),
            'payment_method': self.payment_method,
            'payment_date': self.payment_date.isoformat(),
            'status': self.status,
            'receipt_number': self.receipt_number,
            'remarks': self.remarks,
            'gateway_transaction_id': self.gateway_transaction_id
        })
        return data


class Scholarship(BaseModel):
    """Scholarship for students - Multi-tenant"""
    __tablename__ = 'scholarships'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    scholarship_type = db.Column(db.String(50), nullable=False)  # merit, need-based, sports, etc.
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    percentage = db.Column(db.Float, nullable=True)  # If scholarship is percentage-based
    academic_year = db.Column(db.String(20), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(50), default='active')  # active, inactive, completed
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_on = db.Column(db.DateTime, nullable=True)
    remarks = db.Column(db.Text)
    
    # Relationships
    student = db.relationship('User', foreign_keys=[student_id], backref='scholarships')
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'student_id': self.student_id,
            'student_name': self.student.name,
            'name': self.name,
            'scholarship_type': self.scholarship_type,
            'amount': float(self.amount),
            'percentage': self.percentage,
            'academic_year': self.academic_year,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'approved_by_id': self.approved_by_id,
            'approved_by_name': self.approved_by.name if self.approved_by else None,
            'approved_on': self.approved_on.isoformat() if self.approved_on else None,
            'remarks': self.remarks
        })
        return data
