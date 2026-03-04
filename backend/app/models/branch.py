"""
Multi-Branch Support Models
Allows a single school to manage multiple campuses/branches
"""
from app.models.base import BaseModel
from app.extensions import db
from datetime import datetime


class Branch(BaseModel):
    """Branch/Campus model - Multi-tenant, multi-branch"""
    __tablename__ = 'branches'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(50), nullable=False)  # Short code e.g., "MAIN", "NORTH"
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pincode = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(255))
    principal_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    is_main = db.Column(db.Boolean, default=False)  # Main campus flag
    is_active = db.Column(db.Boolean, default=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    student_capacity = db.Column(db.Integer, default=1000)
    established_date = db.Column(db.Date, nullable=True)

    # Relationships
    school = db.relationship('School', backref='branches')
    principal = db.relationship('User', foreign_keys=[principal_id])

    __table_args__ = (
        db.UniqueConstraint('school_id', 'code', name='uq_school_branch_code'),
        db.UniqueConstraint('school_id', 'name', name='uq_school_branch_name'),
    )

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'name': self.name,
            'code': self.code,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'pincode': self.pincode,
            'phone': self.phone,
            'email': self.email,
            'principal_id': self.principal_id,
            'principal_name': self.principal.name if self.principal else None,
            'is_main': self.is_main,
            'is_active': self.is_active,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'student_capacity': self.student_capacity,
            'established_date': self.established_date.isoformat() if self.established_date else None
        })
        return data

    def __repr__(self):
        return f'<Branch {self.name} ({self.code})>'
