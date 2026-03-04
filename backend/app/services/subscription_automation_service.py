import datetime
from app.extensions import db
from app.models.billing import Subscription, Billing
from app.models.school import School
from app.utils.logging import get_logger

logger = get_logger("subscription_automation")

RENEWAL_GRACE_DAYS = 0
MAX_PAYMENT_RETRIES = 3

def process_subscriptions():
    today = datetime.datetime.utcnow()
    subscriptions = Subscription.query.all()
    for sub in subscriptions:
        if sub.renewal_date and sub.renewal_date < today:
            logger.info(f"Checking subscription {sub.id} for school {sub.school_id}")
            if sub.auto_renew:
                # Create new billing record
                billing = Billing(
                    school_id=sub.school_id,
                    subscription_id=sub.id,
                    invoice_number=f"INV-{sub.school_id}-{int(today.timestamp())}",
                    invoice_date=today,
                    due_date=today + datetime.timedelta(days=7),
                    amount=sub.plan.price_monthly if sub.billing_cycle == 'monthly' else sub.plan.price_annual,
                    currency='INR',
                    payment_status='pending',
                    description='Auto-renewal invoice',
                )
                db.session.add(billing)
                # Extend renewal_date
                if sub.billing_cycle == 'monthly':
                    sub.renewal_date += datetime.timedelta(days=30)
                else:
                    sub.renewal_date += datetime.timedelta(days=365)
                sub.status = 'active'
                logger.info(f"Auto-renewed subscription {sub.id} for school {sub.school_id}")
            else:
                sub.status = 'expired'
                school = School.query.get(sub.school_id)
                if school:
                    school.subscription_status = 'suspended'
                    logger.warning(f"Subscription expired for school {sub.school_id}, school suspended.")
        # Handle payment failures
        for billing in sub.billings:
            if billing.payment_status == 'failed' and billing.retry_count < MAX_PAYMENT_RETRIES:
                billing.retry_count += 1
                logger.warning(f"Retrying payment for billing {billing.id}, attempt {billing.retry_count}")
                # Here you would trigger payment retry logic (integration point)
            elif billing.payment_status == 'failed' and billing.retry_count >= MAX_PAYMENT_RETRIES:
                school = School.query.get(sub.school_id)
                if school and school.subscription_status != 'suspended':
                    school.subscription_status = 'suspended'
                    logger.error(f"School {sub.school_id} suspended after {MAX_PAYMENT_RETRIES} failed payment attempts.")
    db.session.commit()
