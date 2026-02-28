from app.models.base import BaseModel
from app.extensions import db
import enum


class ParentRelation(enum.Enum):
    """Parent relation type enumeration."""
    FATHER = "Father"
    MOTHER = "Mother"
    GUARDIAN = "Guardian"


class CommunicationType(enum.Enum):
    """Communication channel type enumeration."""
    EMAIL = "Email"
    SMS = "SMS"
    CALL = "Call"


class ParentStudent(BaseModel):
    """Association model between parent and student."""
    __tablename__ = 'parent_students'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('parents.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint(
            'school_id',
            'parent_id',
            'student_id',
            name='uq_school_parent_student'
        ),
    )

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'parent_id': self.parent_id,
            'student_id': self.student_id
        })
        return data


class Parent(BaseModel):
    """Parent model - Multi-tenant."""
    __tablename__ = 'parents'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255))
    phone = db.Column(db.String(20), nullable=False)
    secondary_phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    occupation = db.Column(db.String(255))
    relation_to_student = db.Column(
        db.Enum(ParentRelation),
        nullable=False,
        default=ParentRelation.GUARDIAN
    )

    students = db.relationship(
        'Student',
        secondary='parent_students',
        back_populates='parents',
        lazy='select'
    )
    emergency_contacts = db.relationship(
        'EmergencyContact',
        backref='parent',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    communications = db.relationship(
        'CommunicationHistory',
        backref='parent',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    __table_args__ = (
        db.Index('idx_parent_school_phone', 'school_id', 'phone'),
    )

    def to_dict(self, include_relations=False):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'secondary_phone': self.secondary_phone,
            'address': self.address,
            'occupation': self.occupation,
            'relation_to_student': (
                self.relation_to_student.value
                if self.relation_to_student else None
            )
        })

        if include_relations:
            data['students'] = [student.to_dict() for student in self.students]
            data['emergency_contacts'] = [
                contact.to_dict() for contact in self.emergency_contacts.all()
            ]

        return data


class EmergencyContact(BaseModel):
    """Emergency contacts for a parent."""
    __tablename__ = 'emergency_contacts'

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('parents.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    relationship = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'parent_id': self.parent_id,
            'name': self.name,
            'phone': self.phone,
            'relationship': self.relationship
        })
        return data


class CommunicationHistory(BaseModel):
    """Communication history with parent."""
    __tablename__ = 'communication_history'

    parent_id = db.Column(db.Integer, db.ForeignKey('parents.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    type = db.Column(db.Enum(CommunicationType), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, nullable=False)
    sent_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    sent_by_user = db.relationship('User', backref='parent_communications')

    __table_args__ = (
        db.Index('idx_comm_school_parent_sent_at', 'school_id', 'parent_id', 'sent_at'),
    )

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'parent_id': self.parent_id,
            'school_id': self.school_id,
            'type': self.type.value if self.type else None,
            'subject': self.subject,
            'content': self.content,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'sent_by': self.sent_by
        })
        return data
