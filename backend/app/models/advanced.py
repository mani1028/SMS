"""
Advanced Feature Models
- Student Digital ID Cards (QR-based)
- Auto Promotion System
- API Access Keys for Schools
- Document Vault
"""
from app.models.base import BaseModel
from app.extensions import db
from datetime import datetime
import uuid
import hashlib


# ==================== STUDENT DIGITAL ID CARDS ====================

class StudentIDCard(BaseModel):
    """Student digital ID card with QR code - Multi-tenant"""
    __tablename__ = 'student_id_cards'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    card_number = db.Column(db.String(50), nullable=False, unique=True)
    qr_code_data = db.Column(db.String(500), nullable=False)  # Encoded QR data
    academic_year = db.Column(db.String(20), nullable=False)
    issue_date = db.Column(db.Date, default=lambda: datetime.utcnow().date())
    expiry_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    photo_url = db.Column(db.String(500), nullable=True)
    template = db.Column(db.String(50), default='default')  # Card template style
    printed = db.Column(db.Boolean, default=False)
    printed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    student = db.relationship('Student', backref='id_cards')

    __table_args__ = (
        db.UniqueConstraint('school_id', 'student_id', 'academic_year', name='uq_student_id_card'),
    )

    @staticmethod
    def generate_card_number(school_id, student_id):
        """Generate unique card number"""
        unique = f"{school_id}-{student_id}-{uuid.uuid4().hex[:8]}"
        return f"ID-{unique.upper()}"

    @staticmethod
    def generate_qr_data(school_id, student_id, card_number):
        """Generate QR code data payload"""
        import json
        return json.dumps({
            'school_id': school_id,
            'student_id': student_id,
            'card_number': card_number,
            'type': 'student_id'
        })

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'card_number': self.card_number,
            'qr_code_data': self.qr_code_data,
            'academic_year': self.academic_year,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'is_active': self.is_active,
            'photo_url': self.photo_url,
            'template': self.template,
            'printed': self.printed
        })
        return data


# ==================== AUTO PROMOTION SYSTEM ====================

class PromotionBatch(BaseModel):
    """Batch promotion record - Multi-tenant"""
    __tablename__ = 'promotion_batches'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    from_academic_year = db.Column(db.String(20), nullable=False)
    to_academic_year = db.Column(db.String(20), nullable=False)
    from_class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    to_class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, rolled_back
    total_students = db.Column(db.Integer, default=0)
    promoted_count = db.Column(db.Integer, default=0)
    retained_count = db.Column(db.Integer, default=0)
    initiated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    rollback_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text)

    # Relationships
    from_class = db.relationship('Class', foreign_keys=[from_class_id])
    to_class = db.relationship('Class', foreign_keys=[to_class_id])
    initiated_by = db.relationship('User', foreign_keys=[initiated_by_id])
    records = db.relationship('PromotionRecord', backref='batch', cascade='all, delete-orphan')

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'from_academic_year': self.from_academic_year,
            'to_academic_year': self.to_academic_year,
            'from_class_id': self.from_class_id,
            'from_class_name': self.from_class.name if self.from_class else None,
            'to_class_id': self.to_class_id,
            'to_class_name': self.to_class.name if self.to_class else None,
            'status': self.status,
            'total_students': self.total_students,
            'promoted_count': self.promoted_count,
            'retained_count': self.retained_count,
            'initiated_by_id': self.initiated_by_id,
            'initiated_by_name': self.initiated_by.name if self.initiated_by else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'notes': self.notes
        })
        return data


class PromotionRecord(BaseModel):
    """Individual student promotion record"""
    __tablename__ = 'promotion_records'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('promotion_batches.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    from_class = db.Column(db.String(50), nullable=False)
    from_section = db.Column(db.String(20))
    from_roll_no = db.Column(db.String(50))
    to_class = db.Column(db.String(50), nullable=False)
    to_section = db.Column(db.String(20))
    new_roll_no = db.Column(db.String(50))
    status = db.Column(db.String(20), default='promoted')  # promoted, retained, transferred
    result = db.Column(db.String(50))  # pass, fail, conditional
    percentage = db.Column(db.Float, nullable=True)
    remarks = db.Column(db.Text)

    # Relationships
    student = db.relationship('Student', backref='promotion_records')

    __table_args__ = (
        db.UniqueConstraint('batch_id', 'student_id', name='uq_promotion_student'),
    )

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'batch_id': self.batch_id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'from_class': self.from_class,
            'from_section': self.from_section,
            'from_roll_no': self.from_roll_no,
            'to_class': self.to_class,
            'to_section': self.to_section,
            'new_roll_no': self.new_roll_no,
            'status': self.status,
            'result': self.result,
            'percentage': self.percentage,
            'remarks': self.remarks
        })
        return data


# ==================== API ACCESS FOR SCHOOLS ====================

class APIKey(BaseModel):
    """API key for school external integrations"""
    __tablename__ = 'api_keys'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Biometric System", "Mobile App"
    key = db.Column(db.String(64), nullable=False, unique=True)
    secret_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    permissions = db.Column(db.JSON, default=[])  # List of allowed endpoints/actions
    rate_limit = db.Column(db.Integer, default=1000)  # Requests per hour
    last_used_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Usage tracking
    total_requests = db.Column(db.Integer, default=0)
    requests_today = db.Column(db.Integer, default=0)
    last_reset_date = db.Column(db.Date, nullable=True)

    # IP whitelist
    allowed_ips = db.Column(db.JSON, default=[])  # Empty = all IPs allowed

    # Relationships
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    school = db.relationship('School', backref='api_keys')

    __table_args__ = (
        db.UniqueConstraint('school_id', 'name', name='uq_school_api_key_name'),
    )

    @staticmethod
    def generate_key():
        """Generate a unique API key"""
        return uuid.uuid4().hex + uuid.uuid4().hex[:32]

    @staticmethod
    def hash_secret(secret):
        """Hash API secret"""
        return hashlib.sha256(secret.encode()).hexdigest()

    def verify_secret(self, secret):
        """Verify API secret"""
        return self.secret_hash == hashlib.sha256(secret.encode()).hexdigest()

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'name': self.name,
            'key': self.key[:8] + '...' + self.key[-4:],  # Masked
            'is_active': self.is_active,
            'permissions': self.permissions,
            'rate_limit': self.rate_limit,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'total_requests': self.total_requests,
            'requests_today': self.requests_today,
            'allowed_ips': self.allowed_ips,
            'created_by_id': self.created_by_id
        })
        return data


# ==================== DOCUMENT VAULT ====================

class DocumentVault(BaseModel):
    """Secure document vault - Multi-tenant"""
    __tablename__ = 'document_vault'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    owner_type = db.Column(db.String(50), nullable=False)  # student, staff, school
    owner_id = db.Column(db.Integer, nullable=False)  # student_id or user_id
    category = db.Column(db.String(50), nullable=False)
    # Categories: certificate, transfer, medical, identity, academic, legal, other

    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # In bytes
    mime_type = db.Column(db.String(100))
    file_hash = db.Column(db.String(64))  # SHA-256 for integrity check

    # Access control
    is_confidential = db.Column(db.Boolean, default=False)
    access_roles = db.Column(db.JSON, default=[])  # Roles that can view

    # Verification
    is_verified = db.Column(db.Boolean, default=False)
    verified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)

    # Upload info
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Expiry
    expiry_date = db.Column(db.Date, nullable=True)
    is_expired = db.Column(db.Boolean, default=False)

    # Version
    version = db.Column(db.Integer, default=1)
    parent_doc_id = db.Column(db.Integer, db.ForeignKey('document_vault.id'), nullable=True)

    # Relationships
    uploaded_by = db.relationship('User', foreign_keys=[uploaded_by_id])
    verified_by = db.relationship('User', foreign_keys=[verified_by_id])
    school = db.relationship('School', backref='vault_documents')

    __table_args__ = (
        db.Index('idx_vault_owner', 'school_id', 'owner_type', 'owner_id'),
        db.Index('idx_vault_category', 'school_id', 'category'),
    )

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'owner_type': self.owner_type,
            'owner_id': self.owner_id,
            'category': self.category,
            'title': self.title,
            'description': self.description,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'is_confidential': self.is_confidential,
            'is_verified': self.is_verified,
            'verified_by_id': self.verified_by_id,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'uploaded_by_id': self.uploaded_by_id,
            'uploaded_by_name': self.uploaded_by.name if self.uploaded_by else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'is_expired': self.is_expired,
            'version': self.version
        })
        return data


# ==================== ONLINE FEE PAYMENT ====================

class OnlinePaymentTransaction(BaseModel):
    """Online payment via gateway (Razorpay/Stripe) - Multi-tenant"""
    __tablename__ = 'online_payment_transactions'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    installment_id = db.Column(db.Integer, db.ForeignKey('student_fee_installments.id'), nullable=True)

    # Payment details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='INR')
    gateway = db.Column(db.String(50), nullable=False)  # razorpay, stripe, upi

    # Gateway references
    gateway_order_id = db.Column(db.String(255), nullable=True)  # Razorpay order_id / Stripe session_id
    gateway_payment_id = db.Column(db.String(255), nullable=True)  # Payment ID from gateway
    gateway_signature = db.Column(db.String(500), nullable=True)

    # Status
    status = db.Column(db.String(20), default='initiated')  # initiated, pending, success, failed, refunded
    failure_reason = db.Column(db.Text, nullable=True)

    # Receipt
    receipt_number = db.Column(db.String(50), nullable=True)
    receipt_url = db.Column(db.String(500), nullable=True)

    # Metadata
    payer_name = db.Column(db.String(255))
    payer_email = db.Column(db.String(255))
    payer_phone = db.Column(db.String(20))
    payment_method = db.Column(db.String(50))  # upi, card, netbanking, wallet
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.Text)

    # Refund
    refund_id = db.Column(db.String(255), nullable=True)
    refund_amount = db.Column(db.Numeric(10, 2), nullable=True)
    refund_status = db.Column(db.String(20), nullable=True)
    refunded_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    student = db.relationship('Student', backref='online_payments')
    school = db.relationship('School', backref='online_payments')

    __table_args__ = (
        db.Index('idx_online_payment_school', 'school_id', 'status'),
        db.Index('idx_online_payment_student', 'school_id', 'student_id'),
    )

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'installment_id': self.installment_id,
            'amount': float(self.amount),
            'currency': self.currency,
            'gateway': self.gateway,
            'gateway_order_id': self.gateway_order_id,
            'gateway_payment_id': self.gateway_payment_id,
            'status': self.status,
            'receipt_number': self.receipt_number,
            'payer_name': self.payer_name,
            'payer_email': self.payer_email,
            'payment_method': self.payment_method,
            'refund_amount': float(self.refund_amount) if self.refund_amount else None,
            'refund_status': self.refund_status
        })
        return data
