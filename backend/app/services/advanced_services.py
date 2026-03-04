"""
Advanced Features Service
- Multi-Branch management
- Document Vault
- Student Digital ID Cards
- Auto Promotion System
- API Key Management
- Advanced Reports Generator
"""
from app.models.branch import Branch
from app.models.advanced import (
    StudentIDCard, PromotionBatch, PromotionRecord,
    APIKey, DocumentVault, OnlinePaymentTransaction
)
from app.models.student import Student, AcademicHistory
from app.models.academics import Class, Section
from app.models.user import User
from app.extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func
import uuid
import hashlib
import logging

logger = logging.getLogger(__name__)


# ==================== MULTI-BRANCH SERVICE ====================

class BranchService:
    """Service for multi-branch school management"""

    @staticmethod
    def create_branch(school_id, name, code, address=None, city=None, state=None,
                      pincode=None, phone=None, email=None, principal_id=None,
                      is_main=False, student_capacity=1000):
        """Create a new branch"""
        try:
            branch = Branch(
                school_id=school_id, name=name, code=code.upper(),
                address=address, city=city, state=state, pincode=pincode,
                phone=phone, email=email, principal_id=principal_id,
                is_main=is_main, student_capacity=student_capacity
            )
            db.session.add(branch)
            db.session.commit()
            return {'success': True, 'branch': branch.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Create branch error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_branches(school_id):
        """Get all branches for a school"""
        try:
            branches = Branch.query.filter_by(school_id=school_id, is_active=True).all()
            return {'success': True, 'branches': [b.to_dict() for b in branches]}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_branch(school_id, branch_id):
        """Get branch details"""
        try:
            branch = Branch.query.filter_by(id=branch_id, school_id=school_id).first()
            if not branch:
                return {'success': False, 'error': 'Branch not found'}
            return {'success': True, 'branch': branch.to_dict()}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def update_branch(school_id, branch_id, **kwargs):
        """Update branch details"""
        try:
            branch = Branch.query.filter_by(id=branch_id, school_id=school_id).first()
            if not branch:
                return {'success': False, 'error': 'Branch not found'}

            for key, value in kwargs.items():
                if hasattr(branch, key) and value is not None:
                    setattr(branch, key, value)

            db.session.commit()
            return {'success': True, 'branch': branch.to_dict()}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def delete_branch(school_id, branch_id):
        """Soft delete a branch"""
        try:
            branch = Branch.query.filter_by(id=branch_id, school_id=school_id).first()
            if not branch:
                return {'success': False, 'error': 'Branch not found'}
            if branch.is_main:
                return {'success': False, 'error': 'Cannot delete main branch'}
            branch.is_active = False
            db.session.commit()
            return {'success': True, 'message': 'Branch deactivated'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_branch_stats(school_id, branch_id=None):
        """Get stats per branch or all branches"""
        try:
            branches = Branch.query.filter_by(school_id=school_id, is_active=True).all()
            stats = []
            for b in branches:
                if branch_id and b.id != branch_id:
                    continue
                stats.append({
                    'branch': b.to_dict(),
                    'student_count': Student.query.filter_by(school_id=school_id, is_active=True).count(),
                    'capacity_used': 0  # Would need branch_id on Student model
                })
            return {'success': True, 'stats': stats}
        except Exception as e:
            return {'success': False, 'error': str(e)}


# ==================== DOCUMENT VAULT SERVICE ====================

class DocumentVaultService:
    """Service for secure document storage"""

    @staticmethod
    def upload_document(school_id, owner_type, owner_id, category, title,
                        file_name, file_path, file_size=None, mime_type=None,
                        uploaded_by_id=None, is_confidential=False, description=None,
                        expiry_date=None):
        """Upload a document to the vault"""
        try:
            doc = DocumentVault(
                school_id=school_id,
                owner_type=owner_type,
                owner_id=owner_id,
                category=category,
                title=title,
                description=description,
                file_name=file_name,
                file_path=file_path,
                file_size=file_size,
                mime_type=mime_type,
                is_confidential=is_confidential,
                uploaded_by_id=uploaded_by_id,
                expiry_date=expiry_date
            )
            db.session.add(doc)
            db.session.commit()
            return {'success': True, 'document': doc.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Upload document error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_documents(school_id, owner_type=None, owner_id=None, category=None,
                      page=1, per_page=20):
        """Get documents with filters"""
        try:
            query = DocumentVault.query.filter_by(school_id=school_id)

            if owner_type:
                query = query.filter_by(owner_type=owner_type)
            if owner_id:
                query = query.filter_by(owner_id=owner_id)
            if category:
                query = query.filter_by(category=category)

            query = query.order_by(DocumentVault.created_at.desc())

            total = query.count()
            pages = (total + per_page - 1) // per_page
            docs = query.offset((page - 1) * per_page).limit(per_page).all()

            return {
                'success': True,
                'data': {
                    'documents': [d.to_dict() for d in docs],
                    'total': total,
                    'pages': pages,
                    'current_page': page
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def verify_document(school_id, doc_id, verified_by_id):
        """Verify a document"""
        try:
            doc = DocumentVault.query.filter_by(id=doc_id, school_id=school_id).first()
            if not doc:
                return {'success': False, 'error': 'Document not found'}
            doc.is_verified = True
            doc.verified_by_id = verified_by_id
            doc.verified_at = datetime.utcnow()
            db.session.commit()
            return {'success': True, 'document': doc.to_dict()}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def delete_document(school_id, doc_id):
        """Delete document from vault"""
        try:
            doc = DocumentVault.query.filter_by(id=doc_id, school_id=school_id).first()
            if not doc:
                return {'success': False, 'error': 'Document not found'}
            db.session.delete(doc)
            db.session.commit()
            return {'success': True, 'message': 'Document deleted'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def check_expiring_documents(school_id, days_ahead=30):
        """Check for documents expiring soon"""
        try:
            cutoff = (datetime.utcnow() + timedelta(days=days_ahead)).date()
            expiring = DocumentVault.query.filter(
                DocumentVault.school_id == school_id,
                DocumentVault.expiry_date.isnot(None),
                DocumentVault.expiry_date <= cutoff,
                DocumentVault.is_expired == False
            ).all()
            return {
                'success': True,
                'expiring_documents': [d.to_dict() for d in expiring],
                'count': len(expiring)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


# ==================== STUDENT ID CARD SERVICE ====================

class StudentIDCardService:
    """Service for digital student ID cards with QR"""

    @staticmethod
    def generate_id_card(school_id, student_id, academic_year, template='default'):
        """Generate a digital ID card for a student"""
        try:
            student = Student.query.filter_by(school_id=school_id, id=student_id).first()
            if not student:
                return {'success': False, 'error': 'Student not found'}

            # Check if card exists for this year
            existing = StudentIDCard.query.filter_by(
                school_id=school_id, student_id=student_id,
                academic_year=academic_year
            ).first()
            if existing:
                return {'success': True, 'id_card': existing.to_dict(), 'message': 'Card already exists'}

            card_number = StudentIDCard.generate_card_number(school_id, student_id)
            qr_data = StudentIDCard.generate_qr_data(school_id, student_id, card_number)

            card = StudentIDCard(
                school_id=school_id,
                student_id=student_id,
                card_number=card_number,
                qr_code_data=qr_data,
                academic_year=academic_year,
                template=template,
                expiry_date=(datetime.utcnow() + timedelta(days=365)).date()
            )
            db.session.add(card)
            db.session.commit()

            return {'success': True, 'id_card': card.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Generate ID card error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def bulk_generate_cards(school_id, class_name, academic_year, template='default'):
        """Generate ID cards for all students in a class"""
        try:
            students = Student.query.filter_by(
                school_id=school_id, class_name=class_name, is_active=True
            ).all()

            generated = 0
            skipped = 0
            for student in students:
                result = StudentIDCardService.generate_id_card(
                    school_id, student.id, academic_year, template
                )
                if result.get('success'):
                    if 'already exists' in result.get('message', ''):
                        skipped += 1
                    else:
                        generated += 1

            return {
                'success': True,
                'generated': generated,
                'skipped': skipped,
                'total_students': len(students)
            }
        except Exception as e:
            logger.error(f"Bulk generate cards error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def verify_qr_scan(card_number):
        """Verify a QR code scan (for attendance or verification)"""
        try:
            card = StudentIDCard.query.filter_by(card_number=card_number, is_active=True).first()
            if not card:
                return {'success': False, 'error': 'Invalid or inactive card'}

            if card.expiry_date and card.expiry_date < datetime.utcnow().date():
                return {'success': False, 'error': 'Card has expired'}

            student = card.student
            return {
                'success': True,
                'data': {
                    'card': card.to_dict(),
                    'student': student.to_dict() if student else None
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_student_cards(school_id, student_id):
        """Get all ID cards for a student"""
        try:
            cards = StudentIDCard.query.filter_by(
                school_id=school_id, student_id=student_id
            ).order_by(StudentIDCard.created_at.desc()).all()
            return {'success': True, 'cards': [c.to_dict() for c in cards]}
        except Exception as e:
            return {'success': False, 'error': str(e)}


# ==================== AUTO PROMOTION SERVICE ====================

class PromotionService:
    """Service for automatic student promotion at year end"""

    @staticmethod
    def create_promotion_batch(school_id, from_academic_year, to_academic_year,
                               from_class_id, to_class_id, initiated_by_id):
        """Create a promotion batch"""
        try:
            from_class = Class.query.get(from_class_id)
            to_class = Class.query.get(to_class_id)
            if not from_class or not to_class:
                return {'success': False, 'error': 'Invalid class IDs'}

            # Get students in from_class
            students = Student.query.filter_by(
                school_id=school_id,
                class_name=from_class.name,
                is_active=True
            ).all()

            if not students:
                return {'success': False, 'error': 'No students found in this class'}

            batch = PromotionBatch(
                school_id=school_id,
                from_academic_year=from_academic_year,
                to_academic_year=to_academic_year,
                from_class_id=from_class_id,
                to_class_id=to_class_id,
                status='pending',
                total_students=len(students),
                initiated_by_id=initiated_by_id
            )
            db.session.add(batch)
            db.session.flush()

            # Create individual records
            for i, student in enumerate(students):
                record = PromotionRecord(
                    school_id=school_id,
                    batch_id=batch.id,
                    student_id=student.id,
                    from_class=from_class.name,
                    from_section=student.section,
                    from_roll_no=student.roll_no,
                    to_class=to_class.name,
                    status='pending'
                )
                db.session.add(record)

            db.session.commit()
            return {
                'success': True,
                'batch': batch.to_dict(),
                'total_students': len(students)
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Create promotion batch error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def execute_promotion(school_id, batch_id):
        """Execute the promotion - actually promote students"""
        try:
            batch = PromotionBatch.query.filter_by(
                id=batch_id, school_id=school_id
            ).first()
            if not batch:
                return {'success': False, 'error': 'Batch not found'}

            if batch.status != 'pending':
                return {'success': False, 'error': f'Batch is already {batch.status}'}

            batch.status = 'processing'
            db.session.commit()

            promoted = 0
            retained = 0

            records = PromotionRecord.query.filter_by(batch_id=batch.id).all()
            to_class = Class.query.get(batch.to_class_id)

            for record in records:
                student = Student.query.get(record.student_id)
                if not student:
                    continue

                if record.status == 'retained':
                    retained += 1
                    continue

                # Archive current data
                history = AcademicHistory(
                    school_id=school_id,
                    student_id=student.id,
                    class_name=student.class_name,
                    section=student.section,
                    academic_year=batch.from_academic_year,
                    roll_no=student.roll_no,
                    final_result='Promoted'
                )
                db.session.add(history)

                # Promote
                student.class_name = to_class.name if to_class else record.to_class
                student.section = record.to_section  # Can be reassigned
                student.roll_no = record.new_roll_no or f"{promoted + 1}"

                record.status = 'promoted'
                record.new_roll_no = student.roll_no
                promoted += 1

            batch.promoted_count = promoted
            batch.retained_count = retained
            batch.status = 'completed'
            batch.completed_at = datetime.utcnow()
            db.session.commit()

            return {
                'success': True,
                'message': f'Promotion completed: {promoted} promoted, {retained} retained',
                'batch': batch.to_dict()
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Execute promotion error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def rollback_promotion(school_id, batch_id):
        """Rollback a completed promotion"""
        try:
            batch = PromotionBatch.query.filter_by(
                id=batch_id, school_id=school_id, status='completed'
            ).first()
            if not batch:
                return {'success': False, 'error': 'Completed batch not found'}

            records = PromotionRecord.query.filter_by(batch_id=batch.id, status='promoted').all()

            for record in records:
                student = Student.query.get(record.student_id)
                if student:
                    student.class_name = record.from_class
                    student.section = record.from_section
                    student.roll_no = record.from_roll_no
                    record.status = 'rolled_back'

            batch.status = 'rolled_back'
            batch.rollback_at = datetime.utcnow()
            db.session.commit()

            return {'success': True, 'message': 'Promotion rolled back', 'batch': batch.to_dict()}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_promotion_batches(school_id, page=1, per_page=20):
        """Get promotion batch history"""
        try:
            query = PromotionBatch.query.filter_by(school_id=school_id).order_by(
                PromotionBatch.created_at.desc()
            )
            total = query.count()
            pages = (total + per_page - 1) // per_page
            batches = query.offset((page - 1) * per_page).limit(per_page).all()

            return {
                'success': True,
                'data': {
                    'batches': [b.to_dict() for b in batches],
                    'total': total,
                    'pages': pages,
                    'current_page': page
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


# ==================== API KEY SERVICE ====================

class APIKeyService:
    """Service for managing external API access"""

    @staticmethod
    def create_api_key(school_id, name, created_by_id, permissions=None,
                       rate_limit=1000, allowed_ips=None, expires_in_days=365):
        """Create a new API key for a school"""
        try:
            key = APIKey.generate_key()
            secret = uuid.uuid4().hex + uuid.uuid4().hex

            api_key = APIKey(
                school_id=school_id,
                name=name,
                key=key,
                secret_hash=APIKey.hash_secret(secret),
                is_active=True,
                permissions=permissions or ['read'],
                rate_limit=rate_limit,
                expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
                created_by_id=created_by_id,
                allowed_ips=allowed_ips or []
            )
            db.session.add(api_key)
            db.session.commit()

            return {
                'success': True,
                'api_key': {
                    'id': api_key.id,
                    'name': api_key.name,
                    'key': key,  # Show full key only on creation
                    'secret': secret,  # Show secret only on creation – store securely!
                    'permissions': api_key.permissions,
                    'rate_limit': api_key.rate_limit,
                    'expires_at': api_key.expires_at.isoformat()
                },
                'warning': 'Save the key and secret now. The secret will not be shown again.'
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Create API key error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def validate_api_key(key, secret):
        """Validate an API key and secret"""
        try:
            api_key = APIKey.query.filter_by(key=key, is_active=True).first()
            if not api_key:
                return {'success': False, 'error': 'Invalid API key'}

            if not api_key.verify_secret(secret):
                return {'success': False, 'error': 'Invalid API secret'}

            if api_key.expires_at and api_key.expires_at < datetime.utcnow():
                return {'success': False, 'error': 'API key has expired'}

            # Update usage
            today = datetime.utcnow().date()
            if api_key.last_reset_date != today:
                api_key.requests_today = 0
                api_key.last_reset_date = today

            if api_key.requests_today >= api_key.rate_limit:
                return {'success': False, 'error': 'Rate limit exceeded'}

            api_key.total_requests += 1
            api_key.requests_today += 1
            api_key.last_used_at = datetime.utcnow()
            db.session.commit()

            return {
                'success': True,
                'school_id': api_key.school_id,
                'permissions': api_key.permissions,
                'api_key_id': api_key.id
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def list_api_keys(school_id):
        """List all API keys for a school"""
        try:
            keys = APIKey.query.filter_by(school_id=school_id).order_by(
                APIKey.created_at.desc()
            ).all()
            return {'success': True, 'api_keys': [k.to_dict() for k in keys]}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def revoke_api_key(school_id, key_id):
        """Revoke an API key"""
        try:
            api_key = APIKey.query.filter_by(id=key_id, school_id=school_id).first()
            if not api_key:
                return {'success': False, 'error': 'API key not found'}
            api_key.is_active = False
            db.session.commit()
            return {'success': True, 'message': 'API key revoked'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}


# ==================== REPORTS GENERATOR SERVICE ====================

class ReportsService:
    """Advanced report generation with custom filters"""

    @staticmethod
    def generate_student_report(school_id, filters=None):
        """Generate student report with custom filters"""
        try:
            query = Student.query.filter_by(school_id=school_id)

            if filters:
                if filters.get('class_name'):
                    query = query.filter_by(class_name=filters['class_name'])
                if filters.get('section'):
                    query = query.filter_by(section=filters['section'])
                if filters.get('status'):
                    query = query.filter_by(status=filters['status'])
                if filters.get('gender'):
                    query = query.filter_by(gender=filters['gender'])
                if filters.get('is_active') is not None:
                    query = query.filter_by(is_active=filters['is_active'])

            students = query.order_by(Student.class_name, Student.section, Student.name).all()

            report_data = []
            for s in students:
                report_data.append({
                    'admission_no': s.admission_no,
                    'name': s.name,
                    'class': s.class_name,
                    'section': s.section,
                    'roll_no': s.roll_no,
                    'gender': s.gender,
                    'dob': s.dob.isoformat() if s.dob else None,
                    'phone': s.phone,
                    'email': s.email,
                    'parent_name': s.parent_name,
                    'parent_phone': s.parent_phone,
                    'status': s.status.value if s.status else 'active',
                    'admission_date': s.admission_date.isoformat() if s.admission_date else None
                })

            return {
                'success': True,
                'data': {
                    'report_type': 'student_list',
                    'total_records': len(report_data),
                    'filters_applied': filters or {},
                    'records': report_data,
                    'generated_at': datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Student report error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def generate_fee_report(school_id, filters=None):
        """Generate fee collection report"""
        try:
            from app.models.finance import FeePayment, StudentFeeInstallment

            query = StudentFeeInstallment.query.filter_by(school_id=school_id)

            if filters:
                if filters.get('is_paid') is not None:
                    query = query.filter_by(is_paid=filters['is_paid'])
                if filters.get('from_date'):
                    query = query.filter(StudentFeeInstallment.due_date >= filters['from_date'])
                if filters.get('to_date'):
                    query = query.filter(StudentFeeInstallment.due_date <= filters['to_date'])

            installments = query.order_by(StudentFeeInstallment.due_date).all()

            report_data = []
            total_expected = 0
            total_collected = 0
            total_outstanding = 0

            for inst in installments:
                amount = float(inst.amount)
                paid = float(inst.paid_amount)
                outstanding = amount - paid
                total_expected += amount
                total_collected += paid
                total_outstanding += outstanding

                report_data.append({
                    'student_id': inst.student_id,
                    'student_name': inst.student.name if inst.student else None,
                    'installment_number': inst.installment_number,
                    'due_date': inst.due_date.isoformat(),
                    'amount': amount,
                    'paid_amount': paid,
                    'outstanding': outstanding,
                    'is_paid': inst.is_paid,
                    'is_overdue': inst.is_overdue(),
                    'paid_on': inst.paid_on.isoformat() if inst.paid_on else None
                })

            return {
                'success': True,
                'data': {
                    'report_type': 'fee_collection',
                    'total_records': len(report_data),
                    'summary': {
                        'total_expected': total_expected,
                        'total_collected': total_collected,
                        'total_outstanding': total_outstanding,
                        'collection_rate': round((total_collected / total_expected) * 100, 2) if total_expected > 0 else 0
                    },
                    'records': report_data,
                    'generated_at': datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Fee report error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def generate_attendance_report(school_id, filters=None):
        """Generate attendance report"""
        try:
            from app.models.attendance import Attendance, AttendanceStatus

            query = Attendance.query.filter_by(school_id=school_id)

            if filters:
                if filters.get('from_date'):
                    query = query.filter(Attendance.attendance_date >= filters['from_date'])
                if filters.get('to_date'):
                    query = query.filter(Attendance.attendance_date <= filters['to_date'])
                if filters.get('user_id'):
                    query = query.filter_by(user_id=filters['user_id'])

            records = query.order_by(Attendance.attendance_date.desc()).all()

            # Group by user
            user_data = {}
            for r in records:
                uid = r.user_id
                if uid not in user_data:
                    user_data[uid] = {
                        'user_id': uid,
                        'name': r.user.name if r.user else None,
                        'total': 0, 'present': 0, 'absent': 0, 'late': 0
                    }
                user_data[uid]['total'] += 1
                if r.status == AttendanceStatus.PRESENT:
                    user_data[uid]['present'] += 1
                elif r.status == AttendanceStatus.ABSENT:
                    user_data[uid]['absent'] += 1
                elif r.status == AttendanceStatus.LATE:
                    user_data[uid]['late'] += 1

            report_data = []
            for ud in user_data.values():
                ud['percentage'] = round((ud['present'] / ud['total']) * 100, 2) if ud['total'] > 0 else 0
                report_data.append(ud)

            report_data.sort(key=lambda x: x['percentage'])

            return {
                'success': True,
                'data': {
                    'report_type': 'attendance',
                    'total_records': len(report_data),
                    'records': report_data,
                    'generated_at': datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Attendance report error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def generate_exam_report(school_id, exam_term_id, class_id=None):
        """Generate exam results report"""
        try:
            from app.models.exams import GradeBook, ExamSchedule

            query = GradeBook.query.filter_by(
                school_id=school_id, exam_term_id=exam_term_id
            )

            if class_id:
                query = query.join(ExamSchedule).filter(ExamSchedule.class_id == class_id)

            grades = query.all()

            # Build result data
            student_results = {}
            for g in grades:
                sid = g.student_id
                if sid not in student_results:
                    student_results[sid] = {
                        'student_id': sid,
                        'student_name': g.student.name if g.student else None,
                        'subjects': [],
                        'total_marks': 0,
                        'total_max': 0
                    }
                pct = round((g.obtained_marks / g.max_marks) * 100, 2) if g.obtained_marks and g.max_marks else 0
                student_results[sid]['subjects'].append({
                    'subject': g.subject.name if g.subject else None,
                    'obtained': g.obtained_marks,
                    'max': g.max_marks,
                    'percentage': pct,
                    'grade': g.grade
                })
                if g.obtained_marks:
                    student_results[sid]['total_marks'] += g.obtained_marks
                if g.max_marks:
                    student_results[sid]['total_max'] += g.max_marks

            # Calculate overall percentages and rank
            report_data = list(student_results.values())
            for r in report_data:
                r['overall_percentage'] = round(
                    (r['total_marks'] / r['total_max']) * 100, 2
                ) if r['total_max'] > 0 else 0

            report_data.sort(key=lambda x: x['overall_percentage'], reverse=True)
            for i, r in enumerate(report_data):
                r['rank'] = i + 1

            return {
                'success': True,
                'data': {
                    'report_type': 'exam_results',
                    'exam_term_id': exam_term_id,
                    'total_students': len(report_data),
                    'records': report_data,
                    'generated_at': datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Exam report error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def export_csv_data(report_data):
        """Convert report data to CSV format"""
        try:
            import csv
            import io

            records = report_data.get('records', [])
            if not records:
                return {'success': False, 'error': 'No data to export'}

            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=records[0].keys())
            writer.writeheader()

            for record in records:
                # Flatten nested dicts/lists for CSV
                flat_record = {}
                for key, val in record.items():
                    if isinstance(val, (list, dict)):
                        flat_record[key] = str(val)
                    else:
                        flat_record[key] = val
                writer.writerow(flat_record)

            return {
                'success': True,
                'csv_content': output.getvalue(),
                'filename': f"{report_data.get('report_type', 'report')}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        except Exception as e:
            logger.error(f"CSV export error: {str(e)}")
            return {'success': False, 'error': str(e)}
