import hmac
import hashlib
import json
from flask import Blueprint, request, jsonify, current_app
from app.extensions import db
from app.models.billing import Billing, Subscription
from app.models.webhook_log import WebhookLog
from app.utils.logging import get_logger
from datetime import datetime, timedelta

webhook_bp = Blueprint('webhook_bp', __name__)
logger = get_logger("razorpay_webhook")

RAZORPAY_WEBHOOK_SECRET = current_app.config.get('RAZORPAY_WEBHOOK_SECRET', 'changeme')

# Helper: Verify Razorpay signature
def verify_signature(payload, signature):
    generated = hmac.new(
        RAZORPAY_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(generated, signature)

@webhook_bp.route('/api/webhooks/razorpay', methods=['POST'])
def razorpay_webhook():
    signature = request.headers.get('X-Razorpay-Signature')
    payload = request.data
    event = request.json.get('event')
    logger.info(f"Received Razorpay webhook: {event}")

    # Log webhook
    log = WebhookLog(
        event_type=event,
        payload=payload.decode(),
        signature=signature
    )
    db.session.add(log)
    db.session.commit()

    # Verify signature
    if not verify_signature(payload, signature):
        logger.error("Invalid Razorpay webhook signature.")
        return jsonify({'status': False, 'message': 'Invalid signature'}), 400

    # Handle events
    if event == 'payment.captured':
        data = request.json['payload']['payment']['entity']
        billing_id = data.get('notes', {}).get('billing_id')
        if billing_id:
            billing = Billing.query.get(billing_id)
            if billing:
                billing.payment_status = 'paid'
                billing.payment_date = datetime.utcnow()
                db.session.commit()
                # Update subscription
                sub = Subscription.query.get(billing.subscription_id)
                if sub:
                    sub.status = 'active'
                    sub.renewal_date = (sub.renewal_date or datetime.utcnow()) + timedelta(days=30 if sub.billing_cycle == 'monthly' else 365)
                    db.session.commit()
                logger.info(f"Payment captured for billing {billing_id}")
    elif event == 'payment.failed':
        data = request.json['payload']['payment']['entity']
        billing_id = data.get('notes', {}).get('billing_id')
        if billing_id:
            billing = Billing.query.get(billing_id)
            if billing:
                billing.payment_status = 'failed'
                billing.retry_count = (billing.retry_count or 0) + 1
                db.session.commit()
                logger.warning(f"Payment failed for billing {billing_id}")
    elif event == 'subscription.charged':
        # Handle subscription charge event if needed
        logger.info("Subscription charged event received.")
    else:
        logger.info(f"Unhandled Razorpay event: {event}")

    return jsonify({'status': True, 'message': 'Webhook processed'})
