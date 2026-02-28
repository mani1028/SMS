from app.models.base import BaseModel
from app.extensions import db
import enum


class StudentStatus(enum.Enum):
    """Student status enumeration"""
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    TRANSFERRED = 'transferred'
    GRADUATED = 'graduated'


class Student(BaseModel):
    """Student model - Multi-tenant"""
    __tablename__ = 'students'
    
    # Basic Information
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    admission_no = db.Column(db.String(100), nullable=False)
    roll_no = db.Column(db.String(50))
    class_name = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(20))
    
    # Contact Information
    email = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    
    # New Fields - Personal Details
    gender = db.Column(db.String(20))
    dob = db.Column(db.Date)
    blood_group = db.Column(db.String(10))
    address = db.Column(db.Text)
    
    # Academic Details
    previous_school = db.Column(db.String(255))
    admission_date = db.Column(db.Date)
    
    # Status Management
    status = db.Column(db.Enum(StudentStatus), default=StudentStatus.ACTIVE, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Parent/Guardian Information (optional fields for future extension)
    parent_name = db.Column(db.String(255))
    parent_phone = db.Column(db.String(20))
    parent_email = db.Column(db.String(255))
    
    # Relationships
    parents = db.relationship(
        'Parent',
        secondary='parent_students',
        back_populates='students',
        lazy='select'
    )
    academic_history = db.relationship('AcademicHistory', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    documents = db.relationship('StudentDocument', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    
    # Unique constraints
    __table_args__ = (
        db.UniqueConstraint('school_id', 'admission_no', name='uq_school_admission'),
        db.UniqueConstraint('school_id', 'roll_no', 'class_name', name='uq_school_roll_class'),
    )
    
    def to_dict(self, include_relations=False):
        """Convert model to dictionary with optional relations"""
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'name': self.name,
            'admission_no': self.admission_no,
            'roll_no': self.roll_no,
            'class_name': self.class_name,
            'section': self.section,
            'email': self.email,
            'phone': self.phone,
            'gender': self.gender,
            'dob': self.dob.isoformat() if self.dob else None,
            'blood_group': self.blood_group,
            'address': self.address,
            'previous_school': self.previous_school,
            'admission_date': self.admission_date.isoformat() if self.admission_date else None,
            'status': self.status.value if self.status else 'active',
            'is_active': self.is_active,
            'parent_name': self.parent_name,
            'parent_phone': self.parent_phone,
            'parent_email': self.parent_email
        })
        
        if include_relations:
            data['parents'] = [parent.to_dict() for parent in self.parents]
            data['academic_history'] = [ah.to_dict() for ah in self.academic_history.all()]
            data['documents'] = [doc.to_dict() for doc in self.documents.all()]
        
        return data
    
    def __repr__(self):
        return f'<Student {self.admission_no}>'


class AcademicHistory(BaseModel):
    """Academic history model for year-wise student records"""
    __tablename__ = 'academic_history'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    
    # Academic Details
    class_name = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(20))
    academic_year = db.Column(db.String(20), nullable=False)  # e.g., "2025-2026"
    roll_no = db.Column(db.String(50))
    
    # Results (stored as JSON)
    result_data = db.Column(db.JSON)  # Can store grades, marks, attendance, etc.
    
    # Performance Metrics
    attendance_percentage = db.Column(db.Float)
    final_result = db.Column(db.String(50))  # Pass/Fail/Promoted
    remarks = db.Column(db.Text)
    
    # Multi-tenant constraint
    __table_args__ = (
        db.Index('idx_academic_school_student', 'school_id', 'student_id'),
    )
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'student_id': self.student_id,
            'class_name': self.class_name,
            'section': self.section,
            'academic_year': self.academic_year,
            'roll_no': self.roll_no,
            'result_data': self.result_data,
            'attendance_percentage': self.attendance_percentage,
            'final_result': self.final_result,
            'remarks': self.remarks
        })
        return data
    
    def __repr__(self):
        return f'<AcademicHistory Student:{self.student_id} Year:{self.academic_year}>'


class StudentDocument(BaseModel):
    """Student document metadata model"""
    __tablename__ = 'student_documents'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    
    # Document Details
    doc_type = db.Column(db.String(50), nullable=False)  # e.g., 'birth_certificate', 'id_proof', 'photo'
    doc_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # Size in bytes
    mime_type = db.Column(db.String(100))
    
    # Verification
    is_verified = db.Column(db.Boolean, default=False)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    verified_at = db.Column(db.DateTime)
    
    # Multi-tenant constraint
    __table_args__ = (
        db.Index('idx_doc_school_student', 'school_id', 'student_id'),
    )
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'student_id': self.student_id,
            'doc_type': self.doc_type,
            'doc_name': self.doc_name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'is_verified': self.is_verified,
            'verified_by': self.verified_by,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None
        })
        return data
    
    def __repr__(self):
        return f'<StudentDocument {self.doc_type} for Student:{self.student_id}>'
