from app.models.base import BaseModel
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(BaseModel):
    """User model - Multi-tenant"""
    __tablename__ = 'users'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(500), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=True)
    
    # Relationships
    role = db.relationship('Role', backref='users')
    
    # Unique constraint on email per school
    __table_args__ = (db.UniqueConstraint('school_id', 'email', name='uq_school_email'),)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'name': self.name,
            'email': self.email,
            'is_active': self.is_active,
            'role': self.role.to_dict() if self.role else None
        })
        return data
    
    def __repr__(self):
        return f'<User {self.email}>'
