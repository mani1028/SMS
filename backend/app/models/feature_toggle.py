"""
Feature Toggle Models
Enable/disable modules per school based on subscription plan
"""
from app.models.base import BaseModel
from app.extensions import db
from datetime import datetime


# ── Default feature definitions per plan tier ──────────────────
DEFAULT_FEATURES = {
    'students': {'name': 'Student Management', 'plans': ['Free', 'Basic', 'Pro', 'Enterprise']},
    'attendance': {'name': 'Attendance', 'plans': ['Free', 'Basic', 'Pro', 'Enterprise']},
    'academics': {'name': 'Academics & Timetable', 'plans': ['Free', 'Basic', 'Pro', 'Enterprise']},
    'exams': {'name': 'Exams & Grades', 'plans': ['Basic', 'Pro', 'Enterprise']},
    'finance': {'name': 'Fee Management', 'plans': ['Basic', 'Pro', 'Enterprise']},
    'communication': {'name': 'Communication', 'plans': ['Basic', 'Pro', 'Enterprise']},
    'parent_portal': {'name': 'Parent Portal', 'plans': ['Basic', 'Pro', 'Enterprise']},
    'transport': {'name': 'Transport Management', 'plans': ['Pro', 'Enterprise']},
    'hostel': {'name': 'Hostel Management', 'plans': ['Pro', 'Enterprise']},
    'library': {'name': 'Library Management', 'plans': ['Pro', 'Enterprise']},
    'expense': {'name': 'Expense Management', 'plans': ['Pro', 'Enterprise']},
    'payroll': {'name': 'Staff Payroll', 'plans': ['Pro', 'Enterprise']},
    'analytics': {'name': 'Analytics Dashboard', 'plans': ['Pro', 'Enterprise']},
    'curriculum': {'name': 'Curriculum Planner', 'plans': ['Pro', 'Enterprise']},
    'online_payment': {'name': 'Online Payment Gateway', 'plans': ['Pro', 'Enterprise']},
    'alerts': {'name': 'Smart Alerts', 'plans': ['Pro', 'Enterprise']},
    'bulk_operations': {'name': 'Bulk Operations', 'plans': ['Pro', 'Enterprise']},
    'id_cards': {'name': 'Student ID Cards', 'plans': ['Pro', 'Enterprise']},
    'document_vault': {'name': 'Document Vault', 'plans': ['Enterprise']},
    'multi_branch': {'name': 'Multi-Branch', 'plans': ['Enterprise']},
    'api_access': {'name': 'API Access', 'plans': ['Enterprise']},
    'custom_branding': {'name': 'Custom Branding', 'plans': ['Pro', 'Enterprise']},
    'backup_restore': {'name': 'Backup & Restore', 'plans': ['Pro', 'Enterprise']},
    'custom_reports': {'name': 'Custom Reports', 'plans': ['Enterprise']},
    'enquiry_crm': {'name': 'Enquiry CRM', 'plans': ['Basic', 'Pro', 'Enterprise']},
    'audit_logs': {'name': 'Audit Logs', 'plans': ['Pro', 'Enterprise']},
}


class FeatureDefinition(BaseModel):
    """Global feature definition managed by platform admin"""
    __tablename__ = 'feature_definitions'

    key = db.Column(db.String(100), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # core, advanced, premium
    min_plan = db.Column(db.String(50), default='Free')  # minimum plan required
    is_global_enabled = db.Column(db.Boolean, default=True)  # platform-level kill switch
    available_plans = db.Column(db.JSON, default=[])  # list of plan names that include this feature
    icon = db.Column(db.String(50))  # material icon name for UI
    sort_order = db.Column(db.Integer, default=0)

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'key': self.key,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'min_plan': self.min_plan,
            'is_global_enabled': self.is_global_enabled,
            'available_plans': self.available_plans,
            'icon': self.icon,
            'sort_order': self.sort_order
        })
        return data


class SchoolFeatureToggle(BaseModel):
    """Per-school feature toggle override - Multi-tenant"""
    __tablename__ = 'school_feature_toggles'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    feature_key = db.Column(db.String(100), nullable=False)
    is_enabled = db.Column(db.Boolean, default=True)
    enabled_at = db.Column(db.DateTime, nullable=True)
    disabled_at = db.Column(db.DateTime, nullable=True)
    disabled_reason = db.Column(db.Text)
    override_by_admin = db.Column(db.Boolean, default=False)  # True = platform admin override

    __table_args__ = (
        db.UniqueConstraint('school_id', 'feature_key', name='uq_school_feature'),
        db.Index('idx_school_features', 'school_id', 'is_enabled'),
    )

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'feature_key': self.feature_key,
            'is_enabled': self.is_enabled,
            'enabled_at': self.enabled_at.isoformat() if self.enabled_at else None,
            'disabled_at': self.disabled_at.isoformat() if self.disabled_at else None,
            'disabled_reason': self.disabled_reason,
            'override_by_admin': self.override_by_admin
        })
        return data
