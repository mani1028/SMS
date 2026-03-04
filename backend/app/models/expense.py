"""
Expense Management Models
Track school expenses, staff salaries, maintenance costs
"""
from app.models.base import BaseModel
from app.extensions import db
from datetime import datetime


class ExpenseCategory(BaseModel):
    """Expense category - Multi-tenant"""
    __tablename__ = 'expense_categories'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    parent_category_id = db.Column(db.Integer, db.ForeignKey('expense_categories.id'), nullable=True)
    budget_amount = db.Column(db.Numeric(12, 2), default=0)
    is_active = db.Column(db.Boolean, default=True)

    parent_category = db.relationship('ExpenseCategory', remote_side='ExpenseCategory.id', backref='subcategories')
    expenses = db.relationship('Expense', backref='category', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('school_id', 'code', name='uq_expense_category_code'),
    )

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'parent_category_id': self.parent_category_id,
            'budget_amount': float(self.budget_amount) if self.budget_amount else 0,
            'is_active': self.is_active,
            'subcategories': [sc.to_dict() for sc in self.subcategories] if self.subcategories else []
        })
        return data


class Expense(BaseModel):
    """Individual expense record - Multi-tenant"""
    __tablename__ = 'expenses'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_categories.id'), nullable=False)

    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    expense_date = db.Column(db.Date, nullable=False, default=lambda: datetime.utcnow().date())

    payment_method = db.Column(db.String(50), default='cash')  # cash, cheque, bank_transfer, upi
    reference_number = db.Column(db.String(100))
    receipt_url = db.Column(db.String(500))

    vendor_name = db.Column(db.String(255))
    vendor_contact = db.Column(db.String(100))

    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, paid
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    is_recurring = db.Column(db.Boolean, default=False)
    recurring_frequency = db.Column(db.String(20))  # monthly, quarterly, yearly
    next_due_date = db.Column(db.Date, nullable=True)

    tags = db.Column(db.JSON, default=[])

    # Relationships
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])

    __table_args__ = (
        db.Index('idx_expense_school_date', 'school_id', 'expense_date'),
        db.Index('idx_expense_category', 'school_id', 'category_id'),
        db.Index('idx_expense_status', 'school_id', 'status'),
    )

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'branch_id': self.branch_id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'title': self.title,
            'description': self.description,
            'amount': float(self.amount),
            'expense_date': self.expense_date.isoformat() if self.expense_date else None,
            'payment_method': self.payment_method,
            'reference_number': self.reference_number,
            'receipt_url': self.receipt_url,
            'vendor_name': self.vendor_name,
            'vendor_contact': self.vendor_contact,
            'status': self.status,
            'approved_by_id': self.approved_by_id,
            'approved_by_name': self.approved_by.name if self.approved_by else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'created_by_id': self.created_by_id,
            'created_by_name': self.created_by.name if self.created_by else None,
            'is_recurring': self.is_recurring,
            'recurring_frequency': self.recurring_frequency,
            'next_due_date': self.next_due_date.isoformat() if self.next_due_date else None,
            'tags': self.tags
        })
        return data


class SalaryStructure(BaseModel):
    """Staff salary structure template - Multi-tenant"""
    __tablename__ = 'salary_structures'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100))
    basic_salary = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    hra = db.Column(db.Numeric(12, 2), default=0)
    da = db.Column(db.Numeric(12, 2), default=0)
    ta = db.Column(db.Numeric(12, 2), default=0)
    medical_allowance = db.Column(db.Numeric(12, 2), default=0)
    special_allowance = db.Column(db.Numeric(12, 2), default=0)
    pf_deduction = db.Column(db.Numeric(12, 2), default=0)
    tax_deduction = db.Column(db.Numeric(12, 2), default=0)
    other_deductions = db.Column(db.Numeric(12, 2), default=0)
    is_active = db.Column(db.Boolean, default=True)

    __table_args__ = (
        db.UniqueConstraint('school_id', 'name', name='uq_salary_structure_name'),
    )

    @property
    def gross_salary(self):
        return float(self.basic_salary or 0) + float(self.hra or 0) + float(self.da or 0) + \
               float(self.ta or 0) + float(self.medical_allowance or 0) + float(self.special_allowance or 0)

    @property
    def total_deductions(self):
        return float(self.pf_deduction or 0) + float(self.tax_deduction or 0) + float(self.other_deductions or 0)

    @property
    def net_salary(self):
        return self.gross_salary - self.total_deductions

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'name': self.name,
            'designation': self.designation,
            'basic_salary': float(self.basic_salary or 0),
            'hra': float(self.hra or 0),
            'da': float(self.da or 0),
            'ta': float(self.ta or 0),
            'medical_allowance': float(self.medical_allowance or 0),
            'special_allowance': float(self.special_allowance or 0),
            'pf_deduction': float(self.pf_deduction or 0),
            'tax_deduction': float(self.tax_deduction or 0),
            'other_deductions': float(self.other_deductions or 0),
            'gross_salary': self.gross_salary,
            'total_deductions': self.total_deductions,
            'net_salary': self.net_salary,
            'is_active': self.is_active
        })
        return data


class SalaryPayment(BaseModel):
    """Monthly salary payment record - Multi-tenant"""
    __tablename__ = 'salary_payments'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    salary_structure_id = db.Column(db.Integer, db.ForeignKey('salary_structures.id'), nullable=True)

    month = db.Column(db.Integer, nullable=False)  # 1-12
    year = db.Column(db.Integer, nullable=False)

    basic_amount = db.Column(db.Numeric(12, 2), nullable=False)
    allowances = db.Column(db.Numeric(12, 2), default=0)
    deductions = db.Column(db.Numeric(12, 2), default=0)
    bonus = db.Column(db.Numeric(12, 2), default=0)
    net_amount = db.Column(db.Numeric(12, 2), nullable=False)

    payment_date = db.Column(db.Date, nullable=True)
    payment_method = db.Column(db.String(50))
    transaction_ref = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')  # pending, processed, paid, cancelled
    remarks = db.Column(db.Text)

    processed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relationships
    staff = db.relationship('User', foreign_keys=[staff_id], backref='salary_payments')
    salary_structure = db.relationship('SalaryStructure', backref='payments')
    processed_by = db.relationship('User', foreign_keys=[processed_by_id])

    __table_args__ = (
        db.UniqueConstraint('school_id', 'staff_id', 'month', 'year', name='uq_salary_payment'),
        db.Index('idx_salary_school_month', 'school_id', 'year', 'month'),
    )

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'staff_id': self.staff_id,
            'staff_name': self.staff.name if self.staff else None,
            'salary_structure_id': self.salary_structure_id,
            'month': self.month,
            'year': self.year,
            'basic_amount': float(self.basic_amount),
            'allowances': float(self.allowances or 0),
            'deductions': float(self.deductions or 0),
            'bonus': float(self.bonus or 0),
            'net_amount': float(self.net_amount),
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'payment_method': self.payment_method,
            'transaction_ref': self.transaction_ref,
            'status': self.status,
            'remarks': self.remarks,
            'processed_by_id': self.processed_by_id
        })
        return data
