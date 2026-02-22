from app.models.base import BaseModel
from app.extensions import db


class Student(BaseModel):
    """Student model - Multi-tenant"""
    __tablename__ = 'students'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    admission_no = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    
    # Unique constraint on admission_no per school
    __table_args__ = (db.UniqueConstraint('school_id', 'admission_no', name='uq_school_admission'),)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'name': self.name,
            'admission_no': self.admission_no,
            'class_name': self.class_name,
            'email': self.email,
            'phone': self.phone,
            'is_active': self.is_active
        })
        return data
    
    def __repr__(self):
        return f'<Student {self.admission_no}>'
