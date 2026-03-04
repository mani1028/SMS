"""
Payment Gateway Service
Integration with Razorpay/Stripe for online fee payments
Auto receipt generation and payment tracking
"""
from app.models.advanced import OnlinePaymentTransaction
from app.models.finance import StudentFeeInstallment, FeePayment, PaymentStatus
from app.models.student import Student
from app.models.settings import SchoolConfiguration
from app.extensions import db
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class PaymentGatewayService:
    """Service for online payment gateway integration"""

    @staticmethod
    def initiate_payment(school_id, student_id, installment_id, amount, gateway='razorpay',
                         payer_name=None, payer_email=None, payer_phone=None):
        """
        Initiate online payment - creates order with gateway
        Returns order details for frontend to complete payment
        """
        try:
            student = Student.query.filter_by(school_id=school_id, id=student_id).first()
            if not student:
                return {'success': False, 'error': 'Student not found'}

            installment = None
            if installment_id:
                installment = StudentFeeInstallment.query.get(installment_id)
                if not installment or installment.school_id != school_id:
                    return {'success': False, 'error': 'Installment not found'}
                if installment.is_paid:
                    return {'success': False, 'error': 'Installment already paid'}

            # Get school payment config
            config = SchoolConfiguration.query.filter_by(school_id=school_id).first()

            # Generate internal order ID
            order_id = f"ORD-{school_id}-{uuid.uuid4().hex[:12].upper()}"
            receipt_number = f"RCT-{school_id}-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

            # Create gateway order (simulated - replace with actual gateway SDK calls)
            gateway_order = None
            if gateway == 'razorpay':
                gateway_order = PaymentGatewayService._create_razorpay_order(
                    amount, order_id, config
                )
            elif gateway == 'stripe':
                gateway_order = PaymentGatewayService._create_stripe_session(
                    amount, order_id, config
                )

            # Create transaction record
            transaction = OnlinePaymentTransaction(
                school_id=school_id,
                student_id=student_id,
                installment_id=installment_id,
                amount=amount,
                gateway=gateway,
                gateway_order_id=gateway_order.get('order_id') if gateway_order else order_id,
                status='initiated',
                receipt_number=receipt_number,
                payer_name=payer_name or student.parent_name or student.name,
                payer_email=payer_email or student.parent_email or student.email,
                payer_phone=payer_phone or student.parent_phone or student.phone
            )
            db.session.add(transaction)
            db.session.commit()

            return {
                'success': True,
                'data': {
                    'transaction_id': transaction.id,
                    'order_id': transaction.gateway_order_id,
                    'amount': float(amount),
                    'currency': 'INR',
                    'gateway': gateway,
                    'gateway_config': {
                        'key': config.payment_gateway_key if config else None,
                        'order_id': transaction.gateway_order_id,
                        'amount': int(float(amount) * 100),  # Amount in paise for Razorpay
                        'name': payer_name or student.name,
                        'email': payer_email or student.email,
                        'phone': payer_phone or student.phone
                    },
                    'receipt_number': receipt_number
                }
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Initiate payment error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def verify_payment(school_id, transaction_id, gateway_payment_id, gateway_signature=None):
        """
        Verify payment after gateway callback
        Updates installment and creates fee payment record
        """
        try:
            transaction = OnlinePaymentTransaction.query.filter_by(
                id=transaction_id, school_id=school_id
            ).first()

            if not transaction:
                return {'success': False, 'error': 'Transaction not found'}

            if transaction.status == 'success':
                return {'success': False, 'error': 'Payment already verified'}

            # Verify with gateway (simulated - replace with actual verification)
            verified = True  # In production, verify signature with gateway SDK

            if verified:
                transaction.gateway_payment_id = gateway_payment_id
                transaction.gateway_signature = gateway_signature
                transaction.status = 'success'

                # Update installment as paid
                if transaction.installment_id:
                    installment = StudentFeeInstallment.query.get(transaction.installment_id)
                    if installment:
                        installment.paid_amount = installment.amount
                        installment.is_paid = True
                        installment.paid_on = datetime.utcnow().date()

                # Create fee payment record
                fee_payment = FeePayment(
                    school_id=school_id,
                    student_id=transaction.student_id,
                    installment_id=transaction.installment_id,
                    transaction_id=f"TXN-{gateway_payment_id}",
                    amount=transaction.amount,
                    payment_method='online',
                    payment_date=datetime.utcnow(),
                    status=PaymentStatus.SUCCESS,
                    receipt_number=transaction.receipt_number,
                    gateway_transaction_id=gateway_payment_id,
                    remarks=f"Online payment via {transaction.gateway}"
                )
                db.session.add(fee_payment)
                db.session.commit()

                return {
                    'success': True,
                    'message': 'Payment verified successfully',
                    'data': {
                        'transaction': transaction.to_dict(),
                        'receipt_number': transaction.receipt_number
                    }
                }
            else:
                transaction.status = 'failed'
                transaction.failure_reason = 'Signature verification failed'
                db.session.commit()
                return {'success': False, 'error': 'Payment verification failed'}

        except Exception as e:
            db.session.rollback()
            logger.error(f"Verify payment error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def handle_webhook(gateway, payload):
        """Handle payment gateway webhook callbacks"""
        try:
            if gateway == 'razorpay':
                return PaymentGatewayService._handle_razorpay_webhook(payload)
            elif gateway == 'stripe':
                return PaymentGatewayService._handle_stripe_webhook(payload)
            return {'success': False, 'error': 'Unknown gateway'}
        except Exception as e:
            logger.error(f"Webhook error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_payment_history(school_id, student_id=None, page=1, per_page=20,
                            status=None, start_date=None, end_date=None):
        """Get online payment history"""
        try:
            query = OnlinePaymentTransaction.query.filter_by(school_id=school_id)

            if student_id:
                query = query.filter_by(student_id=student_id)
            if status:
                query = query.filter_by(status=status)
            if start_date:
                query = query.filter(OnlinePaymentTransaction.created_at >= start_date)
            if end_date:
                query = query.filter(OnlinePaymentTransaction.created_at <= end_date)

            query = query.order_by(OnlinePaymentTransaction.created_at.desc())

            total = query.count()
            pages = (total + per_page - 1) // per_page
            transactions = query.offset((page - 1) * per_page).limit(per_page).all()

            return {
                'success': True,
                'data': {
                    'transactions': [t.to_dict() for t in transactions],
                    'total': total,
                    'pages': pages,
                    'current_page': page
                }
            }
        except Exception as e:
            logger.error(f"Payment history error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def initiate_refund(school_id, transaction_id, amount=None, reason=None):
        """Initiate refund for an online payment"""
        try:
            transaction = OnlinePaymentTransaction.query.filter_by(
                id=transaction_id, school_id=school_id
            ).first()

            if not transaction:
                return {'success': False, 'error': 'Transaction not found'}

            if transaction.status != 'success':
                return {'success': False, 'error': 'Can only refund successful payments'}

            refund_amount = amount or transaction.amount

            # Process refund with gateway (simulated)
            refund_id = f"RFND-{uuid.uuid4().hex[:12].upper()}"

            transaction.refund_id = refund_id
            transaction.refund_amount = refund_amount
            transaction.refund_status = 'processed'
            transaction.refunded_at = datetime.utcnow()
            transaction.status = 'refunded'

            # Update installment
            if transaction.installment_id:
                installment = StudentFeeInstallment.query.get(transaction.installment_id)
                if installment:
                    installment.paid_amount = float(installment.paid_amount) - float(refund_amount)
                    installment.is_paid = float(installment.paid_amount) >= float(installment.amount)

            db.session.commit()

            return {
                'success': True,
                'message': 'Refund initiated successfully',
                'data': {
                    'refund_id': refund_id,
                    'refund_amount': float(refund_amount),
                    'transaction': transaction.to_dict()
                }
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Refund error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_payment_analytics(school_id, days=30):
        """Get payment analytics for dashboard"""
        try:
            from sqlalchemy import func
            cutoff = datetime.utcnow() - __import__('datetime').timedelta(days=days)

            total_transactions = OnlinePaymentTransaction.query.filter(
                OnlinePaymentTransaction.school_id == school_id,
                OnlinePaymentTransaction.created_at >= cutoff
            ).count()

            successful = OnlinePaymentTransaction.query.filter(
                OnlinePaymentTransaction.school_id == school_id,
                OnlinePaymentTransaction.status == 'success',
                OnlinePaymentTransaction.created_at >= cutoff
            ).count()

            total_amount = db.session.query(
                func.sum(OnlinePaymentTransaction.amount)
            ).filter(
                OnlinePaymentTransaction.school_id == school_id,
                OnlinePaymentTransaction.status == 'success',
                OnlinePaymentTransaction.created_at >= cutoff
            ).scalar() or 0

            failed = OnlinePaymentTransaction.query.filter(
                OnlinePaymentTransaction.school_id == school_id,
                OnlinePaymentTransaction.status == 'failed',
                OnlinePaymentTransaction.created_at >= cutoff
            ).count()

            # Gateway breakdown
            gateway_stats = db.session.query(
                OnlinePaymentTransaction.gateway,
                func.count(OnlinePaymentTransaction.id).label('count'),
                func.sum(OnlinePaymentTransaction.amount).label('total')
            ).filter(
                OnlinePaymentTransaction.school_id == school_id,
                OnlinePaymentTransaction.status == 'success',
                OnlinePaymentTransaction.created_at >= cutoff
            ).group_by(OnlinePaymentTransaction.gateway).all()

            return {
                'success': True,
                'data': {
                    'total_transactions': total_transactions,
                    'successful_payments': successful,
                    'failed_payments': failed,
                    'total_collected': float(total_amount),
                    'success_rate': round((successful / total_transactions) * 100, 2) if total_transactions > 0 else 0,
                    'gateway_breakdown': [{
                        'gateway': g.gateway, 'count': g.count, 'total': float(g.total) if g.total else 0
                    } for g in gateway_stats],
                    'period_days': days
                }
            }
        except Exception as e:
            logger.error(f"Payment analytics error: {str(e)}")
            return {'success': False, 'error': str(e)}

    # ==================== GATEWAY HELPERS (Replace with actual SDK) ====================

    @staticmethod
    def _create_razorpay_order(amount, order_id, config):
        """Create Razorpay order (simulated - replace with actual SDK)"""
        # In production:
        # import razorpay
        # client = razorpay.Client(auth=(config.payment_gateway_key, config.payment_gateway_secret))
        # order = client.order.create({'amount': int(amount * 100), 'currency': 'INR', 'receipt': order_id})
        return {
            'order_id': f"rzp_order_{uuid.uuid4().hex[:16]}",
            'amount': int(float(amount) * 100),
            'currency': 'INR'
        }

    @staticmethod
    def _create_stripe_session(amount, order_id, config):
        """Create Stripe checkout session (simulated - replace with actual SDK)"""
        # In production:
        # import stripe
        # stripe.api_key = config.payment_gateway_secret
        # session = stripe.checkout.Session.create(...)
        return {
            'order_id': f"cs_{uuid.uuid4().hex[:24]}",
            'amount': int(float(amount) * 100),
            'currency': 'INR'
        }

    @staticmethod
    def _handle_razorpay_webhook(payload):
        """Handle Razorpay webhook (simulated)"""
        event = payload.get('event')
        if event == 'payment.captured':
            payment_id = payload.get('payload', {}).get('payment', {}).get('entity', {}).get('id')
            order_id = payload.get('payload', {}).get('payment', {}).get('entity', {}).get('order_id')

            transaction = OnlinePaymentTransaction.query.filter_by(
                gateway_order_id=order_id
            ).first()

            if transaction and transaction.status != 'success':
                transaction.gateway_payment_id = payment_id
                transaction.status = 'success'
                db.session.commit()

        return {'success': True}

    @staticmethod
    def _handle_stripe_webhook(payload):
        """Handle Stripe webhook (simulated)"""
        event_type = payload.get('type')
        if event_type == 'checkout.session.completed':
            session_id = payload.get('data', {}).get('object', {}).get('id')

            transaction = OnlinePaymentTransaction.query.filter_by(
                gateway_order_id=session_id
            ).first()

            if transaction and transaction.status != 'success':
                transaction.status = 'success'
                db.session.commit()

        return {'success': True}
