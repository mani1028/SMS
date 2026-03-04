"""
Finance Service - CRUD and business logic for fees and payments
"""

from app.models.finance import (FeeStructure, FeeComponent, FeePlan, StudentFeeInstallment,
                                FeePayment, Scholarship, PaymentStatus, PaymentMethod)
from app.extensions import db
from datetime import datetime, date, timedelta
import logging
import uuid

logger = logging.getLogger(__name__)


class FeeService:
    """Service for fee management"""
    
    @staticmethod
    def create_fee_structure(school_id, name, academic_year, class_id=None, description=None):
        """Create a fee structure"""
        try:
            existing = FeeStructure.query.filter_by(
                school_id=school_id,
                name=name,
                academic_year=academic_year
            ).first()
            
            if existing:
                return {'success': False, 'error': 'Fee structure already exists'}
            
            structure = FeeStructure(
                school_id=school_id,
                name=name,
                class_id=class_id,
                academic_year=academic_year,
                description=description
            )
            db.session.add(structure)
            db.session.commit()
            
            return {'success': True, 'fee_structure': structure.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating fee structure: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def add_fee_component(school_id, fee_structure_id, fee_type, amount, description=None):
        """Add fee component to structure"""
        try:
            structure = FeeStructure.query.filter_by(id=fee_structure_id, school_id=school_id).first()
            if not structure:
                return {'success': False, 'error': 'Fee structure not found'}
            
            component = FeeComponent(
                school_id=school_id,
                fee_structure_id=fee_structure_id,
                fee_type=fee_type,
                amount=amount,
                description=description
            )
            db.session.add(component)
            db.session.commit()
            
            return {'success': True, 'component': component.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding fee component: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_fee_structures(school_id, page=1, limit=50):
        """Get all fee structures"""
        try:
            query = FeeStructure.query.filter_by(school_id=school_id, is_active=True)
            total = query.count()
            pages = (total + limit - 1) // limit
            
            structures = query.offset((page - 1) * limit).limit(limit).all()
            return {
                'success': True,
                'structures': [s.to_dict() for s in structures],
                'total': total,
                'pages': pages
            }
        except Exception as e:
            logger.error(f"Error getting fee structures: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def create_fee_plan(school_id, fee_structure_id, name, plan_type, number_of_installments=1):
        """Create fee plan"""
        try:
            plan = FeePlan(
                school_id=school_id,
                fee_structure_id=fee_structure_id,
                name=name,
                plan_type=plan_type,
                number_of_installments=number_of_installments
            )
            db.session.add(plan)
            db.session.commit()
            
            return {'success': True, 'plan': plan.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating fee plan: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def assign_fee_to_student(school_id, student_id, fee_plan_id, start_date=None):
        """Assign fee plan to student and create installments"""
        try:
            if not start_date:
                start_date = date.today()
            
            plan = FeePlan.query.filter_by(id=fee_plan_id, school_id=school_id).first()
            if not plan:
                return {'success': False, 'error': 'Fee plan not found'}
            
            # Get total amount from fee structure
            total_amount = plan.fee_structure.get_total_amount()
            installment_amount = total_amount / plan.number_of_installments
            
            # Create installments
            installments = []
            for i in range(1, plan.number_of_installments + 1):
                # Calculate due date based on plan type
                if plan.plan_type == 'monthly':
                    due_date = start_date + timedelta(days=30 * i)
                elif plan.plan_type == 'quarterly':
                    due_date = start_date + timedelta(days=90 * i)
                elif plan.plan_type == 'semester':
                    due_date = start_date + timedelta(days=180 * i)
                else:  # full or installment
                    due_date = start_date + timedelta(days=30 * i)
                
                installment = StudentFeeInstallment(
                    school_id=school_id,
                    student_id=student_id,
                    fee_plan_id=fee_plan_id,
                    installment_number=i,
                    due_date=due_date,
                    amount=installment_amount
                )
                db.session.add(installment)
                installments.append(installment)
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Installments created for student',
                'installments': [inst.to_dict() for inst in installments]
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error assigning fee: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_student_fees(school_id, student_id):
        """Get all fees for a student"""
        try:
            installments = StudentFeeInstallment.query.filter_by(
                school_id=school_id,
                student_id=student_id
            ).all()
            
            # Calculate totals
            total_due = sum(inst.amount for inst in installments)
            total_paid = sum(inst.paid_amount for inst in installments)
            outstanding = total_due - total_paid
            
            return {
                'success': True,
                'fees': {
                    'installments': [i.to_dict() for i in installments],
                    'total_due': float(total_due),
                    'total_paid': float(total_paid),
                    'outstanding': float(outstanding),
                    'is_defaulter': outstanding > 0
                }
            }
        except Exception as e:
            logger.error(f"Error getting student fees: {str(e)}")
            return {'success': False, 'error': str(e)}


class PaymentService:
    """Service for payment processing"""
    
    @staticmethod
    def process_payment(school_id, student_id, installment_id, amount, payment_method, remarks=None):
        """Process a fee payment"""
        try:
            installment = StudentFeeInstallment.query.filter_by(
                id=installment_id,
                school_id=school_id,
                student_id=student_id
            ).first()
            
            if not installment:
                return {'success': False, 'error': 'Installment not found'}
            
            # Check if amount exceeds outstanding
            outstanding = float(installment.amount) - float(installment.paid_amount)
            if amount > outstanding:
                return {'success': False, 'error': f'Amount exceeds outstanding balance of {outstanding}'}
            
            # Generate transaction ID
            transaction_id = f"TXN{school_id}{student_id}{int(datetime.utcnow().timestamp())}"
            
            # Create payment record
            payment = FeePayment(
                school_id=school_id,
                student_id=student_id,
                installment_id=installment_id,
                transaction_id=transaction_id,
                amount=amount,
                payment_method=payment_method,
                status=PaymentStatus.SUCCESS,
                payment_date=datetime.utcnow(),
                remarks=remarks
            )
            
            # Update installment
            installment.paid_amount += amount
            if installment.paid_amount >= installment.amount:
                installment.is_paid = True
                installment.paid_on = date.today()
            
            db.session.add(payment)
            db.session.commit()
            
            return {
                'success': True,
                'payment': payment.to_dict(),
                'installment': installment.to_dict(),
                'receipt_number': f"RCP{transaction_id[-8:]}"
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing payment: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_payments(school_id, student_id=None, page=1, limit=50):
        """Get payment records"""
        try:
            query = FeePayment.query.filter_by(school_id=school_id)
            
            if student_id:
                query = query.filter_by(student_id=student_id)
            
            total = query.count()
            pages = (total + limit - 1) // limit
            
            payments = query.offset((page - 1) * limit).limit(limit).order_by(
                FeePayment.payment_date.desc()
            ).all()
            
            return {
                'success': True,
                'payments': [p.to_dict() for p in payments],
                'total': total,
                'pages': pages
            }
        except Exception as e:
            logger.error(f"Error getting payments: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_collection_report(school_id, from_date=None, to_date=None):
        """Get fee collection report"""
        try:
            if not from_date:
                from_date = date(date.today().year, 1, 1)
            if not to_date:
                to_date = date.today()
            
            query = FeePayment.query.filter(
                FeePayment.school_id == school_id,
                FeePayment.payment_date >= from_date,
                FeePayment.payment_date <= to_date + timedelta(days=1)
            )
            
            total_collection = sum(float(p.amount) for p in query.all())
            transaction_count = query.count()
            
            # Get defaulters
            defaulters = db.session.query(StudentFeeInstallment.student_id).filter(
                StudentFeeInstallment.school_id == school_id,
                StudentFeeInstallment.is_paid == False,
                StudentFeeInstallment.due_date < date.today()
            ).distinct().count()
            
            return {
                'success': True,
                'report': {
                    'from_date': from_date.isoformat(),
                    'to_date': to_date.isoformat(),
                    'total_collection': float(total_collection),
                    'transaction_count': transaction_count,
                    'payment_methods': {},
                    'defaulters': defaulters
                }
            }
        except Exception as e:
            logger.error(f"Error getting collection report: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_defaulters(school_id):
        """Get list of fee defaulters"""
        try:
            # Find students with overdue unpaid installments
            from app.models.user import User
            
            defaulter_ids = db.session.query(StudentFeeInstallment.student_id).filter(
                StudentFeeInstallment.school_id == school_id,
                StudentFeeInstallment.is_paid == False,
                StudentFeeInstallment.due_date < date.today()
            ).distinct().all()
            
            defaulter_ids = [d[0] for d in defaulter_ids]
            defaulters = []
            
            for student_id in defaulter_ids:
                student = User.query.filter_by(id=student_id).first()
                outstanding = db.session.query(
                    db.func.sum(StudentFeeInstallment.amount - StudentFeeInstallment.paid_amount)
                ).filter(
                    StudentFeeInstallment.school_id == school_id,
                    StudentFeeInstallment.student_id == student_id
                ).scalar()
                
                defaulters.append({
                    'student_id': student_id,
                    'student_name': student.name if student else 'Unknown',
                    'outstanding_amount': float(outstanding) if outstanding else 0
                })
            
            return {'success': True, 'defaulters': defaulters}
        except Exception as e:
            logger.error(f"Error getting defaulters: {str(e)}")
            return {'success': False, 'error': str(e)}


class ScholarshipService:
    """Service for scholarship management"""
    
    @staticmethod
    def award_scholarship(school_id, student_id, name, scholarship_type, amount, 
                         percentage, start_date, end_date, approved_by_id, remarks=None):
        """Award scholarship to student"""
        try:
            from datetime import datetime
            scholarship = Scholarship(
                school_id=school_id,
                student_id=student_id,
                name=name,
                scholarship_type=scholarship_type,
                amount=amount,
                percentage=percentage,
                academic_year=f"{start_date.year}-{start_date.year + 1}",
                start_date=start_date,
                end_date=end_date,
                status='active',
                approved_by_id=approved_by_id,
                approved_on=datetime.utcnow(),
                remarks=remarks
            )
            db.session.add(scholarship)
            db.session.commit()
            
            return {'success': True, 'scholarship': scholarship.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error awarding scholarship: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_scholarships(school_id, student_id=None, page=1, limit=50):
        """Get scholarships"""
        try:
            query = Scholarship.query.filter_by(school_id=school_id)
            
            if student_id:
                query = query.filter_by(student_id=student_id)
            
            total = query.count()
            pages = (total + limit - 1) // limit
            
            scholarships = query.offset((page - 1) * limit).limit(limit).all()
            return {
                'success': True,
                'scholarships': [s.to_dict() for s in scholarships],
                'total': total,
                'pages': pages
            }
        except Exception as e:
            logger.error(f"Error getting scholarships: {str(e)}")
            return {'success': False, 'error': str(e)}
