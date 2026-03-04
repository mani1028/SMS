from app.models.base import BaseModel
from app.extensions import db


class School(BaseModel):
    """School model - Tenant"""
    __tablename__ = 'schools'
    
    name = db.Column(db.String(255), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    subscription_status = db.Column(db.String(50), default="active")
    logo_url = db.Column(db.String(255))
    primary_color = db.Column(db.String(20))
    custom_domain = db.Column(db.String(255))
    
    # Relationships
    users = db.relationship('User', backref='school', cascade='all, delete-orphan')
    roles = db.relationship('Role', backref='school', cascade='all, delete-orphan')
    students = db.relationship('Student', backref='school', cascade='all, delete-orphan')
    parents = db.relationship('Parent', backref='school', cascade='all, delete-orphan')
    staff_members = db.relationship('Staff', backref='school', cascade='all, delete-orphan')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'name': self.name,
            'email': self.email,
            'subscription_status': self.subscription_status,
            'logo_url': self.logo_url,
            'primary_color': self.primary_color,
            'custom_domain': self.custom_domain
        })
        return data
    
    def __repr__(self):
        return f'<School {self.name}>'
