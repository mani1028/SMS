"""
Enquiry and Lead Management Models
Multi-tenant lead tracking for admission pipeline
"""
from datetime import datetime
from app.extensions import db
from app.models.base import BaseModel


class Enquiry(BaseModel):
    """
    Enquiry model for prospective student leads
    Tracks leads from initial inquiry through admission funnel
    """
    __tablename__ = 'enquiries'
    
    # Multi-tenant isolation
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False, index=True)
    
    # Lead Information
    student_name = db.Column(db.String(100), nullable=False)
    parent_name = db.Column(db.String(100), nullable=False)
    parent_email = db.Column(db.String(120), nullable=True)
    parent_phone = db.Column(db.String(20), nullable=False)
    secondary_phone = db.Column(db.String(20), nullable=True)
    
    # Admission Details
    class_applying_for = db.Column(db.String(50), nullable=False)
    preferred_section = db.Column(db.String(10), nullable=True)
    previous_school = db.Column(db.String(200), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    
    # Lead Status Pipeline
    status = db.Column(db.String(50), default='new', nullable=False, index=True)
    # Statuses: new, contacted, visited, applied, document_pending, admitted, rejected, lost
    
    source = db.Column(db.String(50), nullable=True)
    # Sources: website, walk-in, referral, advertisement, social_media, event
    
    # Follow-up Management
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    next_follow_up = db.Column(db.DateTime, nullable=True, index=True)
    last_contacted = db.Column(db.DateTime, nullable=True)
    
    # Additional Information
    address = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Conversion Tracking
    converted_to_student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    converted_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    
    # Relationships
    school = db.relationship('School', backref='enquiries')
    assigned_staff = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_enquiries')
    converted_student = db.relationship('User', foreign_keys=[converted_to_student_id], backref='enquiry_record')
    follow_ups = db.relationship('FollowUp', back_populates='enquiry', cascade='all, delete-orphan')
    documents = db.relationship('EnquiryDocument', back_populates='enquiry', cascade='all, delete-orphan')
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_enquiry_school_status', 'school_id', 'status'),
        db.Index('idx_enquiry_next_followup', 'school_id', 'next_follow_up'),
    )
    
    def to_dict(self):
        """Convert enquiry to dictionary"""
        base = super().to_dict()
        base.update({
            'school_id': self.school_id,
            'student_name': self.student_name,
            'parent_name': self.parent_name,
            'parent_email': self.parent_email,
            'parent_phone': self.parent_phone,
            'secondary_phone': self.secondary_phone,
            'class_applying_for': self.class_applying_for,
            'preferred_section': self.preferred_section,
            'previous_school': self.previous_school,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'status': self.status,
            'source': self.source,
            'priority': self.priority,
            'assigned_to': self.assigned_to,
            'assigned_staff_name': self.assigned_staff.username if self.assigned_staff else None,
            'next_follow_up': self.next_follow_up.isoformat() if self.next_follow_up else None,
            'last_contacted': self.last_contacted.isoformat() if self.last_contacted else None,
            'address': self.address,
            'notes': self.notes,
            'converted_to_student_id': self.converted_to_student_id,
            'converted_at': self.converted_at.isoformat() if self.converted_at else None,
            'rejection_reason': self.rejection_reason,
            'follow_up_count': len(self.follow_ups) if self.follow_ups else 0,
            'document_count': len(self.documents) if self.documents else 0
        })
        return base


class FollowUp(BaseModel):
    """
    Follow-up activity log for enquiries
    Tracks all interactions with prospective parents
    """
    __tablename__ = 'follow_ups'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False, index=True)
    enquiry_id = db.Column(db.Integer, db.ForeignKey('enquiries.id'), nullable=False, index=True)
    
    # Follow-up Details
    follow_up_type = db.Column(db.String(50), nullable=False)
    # Types: phone_call, email, sms, whatsapp, visit, meeting
    
    follow_up_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    contacted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    status = db.Column(db.String(50), default='completed')
    # Statuses: scheduled, completed, missed, rescheduled
    
    outcome = db.Column(db.String(50), nullable=True)
    # Outcomes: interested, not_interested, requested_callback, scheduled_visit, documents_submitted
    
    notes = db.Column(db.Text, nullable=True)
    
    # Next Action
    schedule_next = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    school = db.relationship('School')
    enquiry = db.relationship('Enquiry', back_populates='follow_ups')
    staff = db.relationship('User', foreign_keys=[contacted_by])
    
    def to_dict(self):
        """Convert follow-up to dictionary"""
        base = super().to_dict()
        base.update({
            'school_id': self.school_id,
            'enquiry_id': self.enquiry_id,
            'follow_up_type': self.follow_up_type,
            'follow_up_date': self.follow_up_date.isoformat() if self.follow_up_date else None,
            'contacted_by': self.contacted_by,
            'contacted_by_name': self.staff.username if self.staff else None,
            'status': self.status,
            'outcome': self.outcome,
            'notes': self.notes,
            'schedule_next': self.schedule_next.isoformat() if self.schedule_next else None
        })
        return base


class EnquiryDocument(BaseModel):
    """
    Document attachments for enquiries
    Stores uploaded documents during admission process
    """
    __tablename__ = 'enquiry_documents'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False, index=True)
    enquiry_id = db.Column(db.Integer, db.ForeignKey('enquiries.id'), nullable=False, index=True)
    
    document_type = db.Column(db.String(50), nullable=False)
    # Types: birth_certificate, previous_report, id_proof, photo, medical_certificate, transfer_certificate
    
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)  # Size in bytes
    mime_type = db.Column(db.String(100), nullable=True)
    
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    verified = db.Column(db.Boolean, default=False)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)
    
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    school = db.relationship('School')
    enquiry = db.relationship('Enquiry', back_populates='documents')
    uploader = db.relationship('User', foreign_keys=[uploaded_by])
    verifier = db.relationship('User', foreign_keys=[verified_by])
    
    def to_dict(self):
        """Convert document to dictionary"""
        base = super().to_dict()
        base.update({
            'school_id': self.school_id,
            'enquiry_id': self.enquiry_id,
            'document_type': self.document_type,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'uploaded_by': self.uploaded_by,
            'uploaded_by_name': self.uploader.username if self.uploader else None,
            'verified': self.verified,
            'verified_by': self.verified_by,
            'verified_by_name': self.verifier.username if self.verifier else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'notes': self.notes
        })
        return base
