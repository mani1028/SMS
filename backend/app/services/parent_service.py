from datetime import datetime
import logging

from app.extensions import db
from app.models.parent import (
    Parent,
    ParentRelation,
    ParentStudent,
    EmergencyContact,
    CommunicationHistory,
    CommunicationType,
)
from app.models.student import Student

logger = logging.getLogger(__name__)


class ParentService:
    """Parent management service layer."""

    @staticmethod
    def create_parent(school_id, payload):
        """Create a parent and link to students."""
        try:
            student_ids = payload.get('student_ids', [])
            relation_raw = payload.get('relation_to_student', 'Guardian')

            if not payload.get('name'):
                return {'success': False, 'error': 'name is required'}
            if not payload.get('phone'):
                return {'success': False, 'error': 'phone is required'}

            try:
                relation_to_student = ParentRelation(relation_raw)
            except ValueError:
                return {
                    'success': False,
                    'error': 'relation_to_student must be Father, Mother, or Guardian'
                }

            parent = Parent(
                school_id=school_id,
                user_id=payload.get('user_id'),
                name=payload.get('name'),
                email=payload.get('email'),
                phone=payload.get('phone'),
                secondary_phone=payload.get('secondary_phone'),
                address=payload.get('address'),
                occupation=payload.get('occupation'),
                relation_to_student=relation_to_student,
            )
            db.session.add(parent)
            db.session.flush()

            for student_id in student_ids:
                student = Student.query.filter_by(
                    id=student_id,
                    school_id=school_id
                ).first()
                if not student:
                    db.session.rollback()
                    return {
                        'success': False,
                        'error': f'Student not found: {student_id}'
                    }

                link = ParentStudent(
                    school_id=school_id,
                    parent_id=parent.id,
                    student_id=student.id
                )
                db.session.add(link)

            contacts = payload.get('emergency_contacts', [])
            for contact in contacts:
                if not contact.get('name') or not contact.get('phone'):
                    db.session.rollback()
                    return {
                        'success': False,
                        'error': 'Emergency contact requires name and phone'
                    }
                emergency_contact = EmergencyContact(
                    school_id=school_id,
                    parent_id=parent.id,
                    name=contact.get('name'),
                    phone=contact.get('phone'),
                    relationship=contact.get('relationship', 'Other'),
                )
                db.session.add(emergency_contact)

            db.session.commit()

            return {
                'success': True,
                'message': 'Parent created successfully',
                'parent': parent.to_dict(include_relations=True)
            }
        except Exception as exc:
            logger.error(f'Create parent error: {str(exc)}')
            db.session.rollback()
            return {'success': False, 'error': str(exc)}

    @staticmethod
    def get_parent_profile(parent_id, school_id):
        """Get parent profile with all linked students."""
        try:
            parent = Parent.query.filter_by(
                id=parent_id,
                school_id=school_id
            ).first()

            if not parent:
                return {
                    'success': False,
                    'error': 'Parent not found',
                    'status_code': 404
                }

            profile = parent.to_dict(include_relations=True)
            profile['communication_count'] = parent.communications.count()

            return {'success': True, 'profile': profile}
        except Exception as exc:
            logger.error(f'Get parent profile error: {str(exc)}')
            return {'success': False, 'error': str(exc)}

    @staticmethod
    def add_communication_log(parent_id, school_id, sent_by, payload):
        """Record parent communication activity."""
        try:
            parent = Parent.query.filter_by(
                id=parent_id,
                school_id=school_id
            ).first()
            if not parent:
                return {
                    'success': False,
                    'error': 'Parent not found',
                    'status_code': 404
                }

            comm_type_raw = payload.get('type')
            subject = payload.get('subject')
            content = payload.get('content')

            if not comm_type_raw or not subject or not content:
                return {
                    'success': False,
                    'error': 'type, subject and content are required'
                }

            try:
                comm_type = CommunicationType(comm_type_raw)
            except ValueError:
                return {
                    'success': False,
                    'error': 'type must be Email, SMS, or Call'
                }

            communication = CommunicationHistory(
                parent_id=parent.id,
                school_id=school_id,
                type=comm_type,
                subject=subject,
                content=content,
                sent_at=datetime.utcnow(),
                sent_by=sent_by,
            )
            db.session.add(communication)
            db.session.commit()

            return {
                'success': True,
                'message': 'Communication logged successfully',
                'communication': communication.to_dict()
            }
        except Exception as exc:
            logger.error(f'Add communication log error: {str(exc)}')
            db.session.rollback()
            return {'success': False, 'error': str(exc)}

    @staticmethod
    def update_emergency_contacts(parent_id, school_id, contacts):
        """Replace emergency contact list for a parent."""
        try:
            parent = Parent.query.filter_by(
                id=parent_id,
                school_id=school_id
            ).first()
            if not parent:
                return {
                    'success': False,
                    'error': 'Parent not found',
                    'status_code': 404
                }

            EmergencyContact.query.filter_by(
                parent_id=parent.id,
                school_id=school_id
            ).delete()

            for contact in contacts:
                if not contact.get('name') or not contact.get('phone'):
                    return {
                        'success': False,
                        'error': 'Each emergency contact requires name and phone'
                    }

                emergency_contact = EmergencyContact(
                    school_id=school_id,
                    parent_id=parent.id,
                    name=contact.get('name'),
                    phone=contact.get('phone'),
                    relationship=contact.get('relationship', 'Other'),
                )
                db.session.add(emergency_contact)

            db.session.commit()
            return {
                'success': True,
                'message': 'Emergency contacts updated successfully',
                'contacts': [c.to_dict() for c in parent.emergency_contacts.all()]
            }
        except Exception as exc:
            logger.error(f'Update emergency contacts error: {str(exc)}')
            db.session.rollback()
            return {'success': False, 'error': str(exc)}

    @staticmethod
    def update_parent(parent_id, school_id, payload):
        """Update parent basic details and emergency contacts."""
        try:
            parent = Parent.query.filter_by(
                id=parent_id,
                school_id=school_id
            ).first()
            if not parent:
                return {
                    'success': False,
                    'error': 'Parent not found',
                    'status_code': 404
                }

            allowed_fields = [
                'name',
                'email',
                'phone',
                'secondary_phone',
                'address',
                'occupation',
                'user_id',
            ]
            for field in allowed_fields:
                if field in payload:
                    setattr(parent, field, payload.get(field))

            if 'relation_to_student' in payload:
                try:
                    parent.relation_to_student = ParentRelation(
                        payload.get('relation_to_student')
                    )
                except ValueError:
                    return {
                        'success': False,
                        'error': 'relation_to_student must be Father, Mother, or Guardian'
                    }

            if 'student_ids' in payload and isinstance(payload.get('student_ids'), list):
                ParentStudent.query.filter_by(
                    parent_id=parent.id,
                    school_id=school_id
                ).delete()

                for student_id in payload.get('student_ids', []):
                    student = Student.query.filter_by(
                        id=student_id,
                        school_id=school_id
                    ).first()
                    if not student:
                        db.session.rollback()
                        return {
                            'success': False,
                            'error': f'Student not found: {student_id}'
                        }

                    db.session.add(ParentStudent(
                        school_id=school_id,
                        parent_id=parent.id,
                        student_id=student.id
                    ))

            if 'emergency_contacts' in payload:
                contacts_result = ParentService.update_emergency_contacts(
                    parent_id=parent.id,
                    school_id=school_id,
                    contacts=payload.get('emergency_contacts', [])
                )
                if not contacts_result.get('success'):
                    return contacts_result

            db.session.commit()
            return {
                'success': True,
                'message': 'Parent updated successfully',
                'parent': parent.to_dict(include_relations=True)
            }
        except Exception as exc:
            logger.error(f'Update parent error: {str(exc)}')
            db.session.rollback()
            return {'success': False, 'error': str(exc)}

    @staticmethod
    def get_communication_history(parent_id, school_id):
        """Get communication history for a parent."""
        try:
            parent = Parent.query.filter_by(
                id=parent_id,
                school_id=school_id
            ).first()
            if not parent:
                return {
                    'success': False,
                    'error': 'Parent not found',
                    'status_code': 404
                }

            records = CommunicationHistory.query.filter_by(
                parent_id=parent.id,
                school_id=school_id
            ).order_by(CommunicationHistory.sent_at.desc()).all()

            return {
                'success': True,
                'communications': [record.to_dict() for record in records]
            }
        except Exception as exc:
            logger.error(f'Get communication history error: {str(exc)}')
            return {'success': False, 'error': str(exc)}
