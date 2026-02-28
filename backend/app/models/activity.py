from app.models.base import BaseModel
from app.extensions import db
from enum import Enum


class ActivityType(Enum):
    """Activity types"""
    STUDENT_CREATED = "student_created"
    STUDENT_UPDATED = "student_updated"
    STUDENT_DELETED = "student_deleted"
    USER_CREATED = "user_created"
    USER_LOGGED_IN = "user_logged_in"
    ROLE_CREATED = "role_created"
    REPORT_GENERATED = "report_generated"
    DATA_EXPORTED = "data_exported"


class Activity(BaseModel):
    """Activity log for audit trail"""
    __tablename__ = 'activities'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    activity_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    entity_type = db.Column(db.String(50))  # 'student', 'user', 'role', etc.
    entity_id = db.Column(db.Integer)
    additional_data = db.Column(db.JSON)  # Additional data as JSON
    ip_address = db.Column(db.String(50))
    
    # Relationships
    user = db.relationship('User', backref='activities')
    
    # Unique constraint
    __table_args__ = (db.Index('idx_school_activity', 'school_id', 'created_at'),)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'user_id': self.user_id,
            'activity_type': self.activity_type,
            'description': self.description,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'user_name': self.user.name if self.user else 'System',
            'user_email': self.user.email if self.user else 'system@school.local'
        })
        return data
    
    def __repr__(self):
        return f'<Activity {self.activity_type} on {self.entity_type}>'
