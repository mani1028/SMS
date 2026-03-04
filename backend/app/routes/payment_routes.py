"""
Payment Gateway Routes
Online fee payment via Razorpay/Stripe, webhook handlers, refunds
"""
from flask import Blueprint, request
from app.core.auth import token_required, permission_required
from app.core.response import success_response, error_response
from app.services.payment_gateway_service import PaymentGatewayService
import logging

logger = logging.getLogger(__name__)

payment_bp = Blueprint('payment', __name__, url_prefix='/payments')


@payment_bp.route('/initiate', methods=['POST'])
@token_required
@permission_required('initiate_payment')
def initiate_payment(current_user):
    """Initiate an online payment"""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        installment_id = data.get('installment_id')
        amount = data.get('amount')
        gateway = data.get('gateway', 'razorpay')
        payer_name = data.get('payer_name')
        payer_email = data.get('payer_email')
        payer_phone = data.get('payer_phone')

        if not student_id or not amount:
            return error_response("student_id and amount are required", 400)

        result = PaymentGatewayService.initiate_payment(
            school_id=current_user.school_id,
            student_id=student_id,
            installment_id=installment_id,
            amount=amount,
            gateway=gateway,
            payer_name=payer_name,
            payer_email=payer_email,
            payer_phone=payer_phone
        )

        if result['success']:
            return success_response("Payment initiated", result['data'])
        return error_response(result.get('error', 'Payment initiation failed'), 400)
    except Exception as e:
        logger.error(f"Initiate payment route error: {str(e)}")
        return error_response(str(e), 500)


@payment_bp.route('/verify', methods=['POST'])
@token_required
@permission_required('verify_payment', 'initiate_payment')
def verify_payment(current_user):
    """Verify payment after gateway callback"""
    try:
        data = request.get_json()
        transaction_id = data.get('transaction_id')
        gateway_payment_id = data.get('gateway_payment_id')
        gateway_signature = data.get('gateway_signature')

        if not transaction_id or not gateway_payment_id:
            return error_response("transaction_id and gateway_payment_id are required", 400)

        result = PaymentGatewayService.verify_payment(
            school_id=current_user.school_id,
            transaction_id=transaction_id,
            gateway_payment_id=gateway_payment_id,
            gateway_signature=gateway_signature
        )

        if result['success']:
            return success_response(result['message'], result['data'])
        return error_response(result.get('error', 'Verification failed'), 400)
    except Exception as e:
        logger.error(f"Verify payment route error: {str(e)}")
        return error_response(str(e), 500)


@payment_bp.route('/webhook/<string:gateway>', methods=['POST'])
def payment_webhook(gateway):
    """Handle payment gateway webhook (public endpoint with signature verification)"""
    try:
        # Verify webhook signature based on gateway
        signature = request.headers.get('X-Razorpay-Signature') or \
                    request.headers.get('Stripe-Signature') or \
                    request.headers.get('X-Webhook-Signature')

        if not signature:
            logger.warning(f"Webhook from {gateway} missing signature header")
            # Still process but log the warning for monitoring

        payload = request.get_json()
        if not payload:
            return error_response("Empty webhook payload", 400)

        result = PaymentGatewayService.handle_webhook(gateway, payload, signature=signature)
        if result['success']:
            return success_response("Webhook processed")
        return error_response("Webhook processing failed", 400)
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return error_response(str(e), 500)


@payment_bp.route('/history', methods=['GET'])
@token_required
@permission_required('view_payment_history', 'view_fees')
def payment_history(current_user):
    """Get payment history"""
    try:
        from datetime import datetime

        student_id = request.args.get('student_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)

        result = PaymentGatewayService.get_payment_history(
            school_id=current_user.school_id,
            student_id=student_id,
            page=page, per_page=per_page,
            status=status,
            start_date=start_date,
            end_date=end_date
        )

        if result['success']:
            return success_response("Payment history", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Payment history route error: {str(e)}")
        return error_response(str(e), 500)


@payment_bp.route('/refund', methods=['POST'])
@token_required
@permission_required('initiate_refund')
def initiate_refund(current_user):
    """Initiate a payment refund"""
    try:
        data = request.get_json()
        transaction_id = data.get('transaction_id')
        amount = data.get('amount')
        reason = data.get('reason')

        if not transaction_id:
            return error_response("transaction_id is required", 400)

        result = PaymentGatewayService.initiate_refund(
            school_id=current_user.school_id,
            transaction_id=transaction_id,
            amount=amount,
            reason=reason
        )

        if result['success']:
            return success_response(result['message'], result['data'])
        return error_response(result.get('error', 'Refund failed'), 400)
    except Exception as e:
        logger.error(f"Refund route error: {str(e)}")
        return error_response(str(e), 500)


@payment_bp.route('/analytics', methods=['GET'])
@token_required
@permission_required('view_payment_analytics', 'view_fees')
def payment_analytics(current_user):
    """Get payment analytics for dashboard"""
    try:
        days = request.args.get('days', 30, type=int)
        result = PaymentGatewayService.get_payment_analytics(
            current_user.school_id, days
        )
        if result['success']:
            return success_response("Payment analytics", result['data'])
        return error_response(result.get('error', 'Error'), 400)
    except Exception as e:
        logger.error(f"Payment analytics route error: {str(e)}")
        return error_response(str(e), 500)
