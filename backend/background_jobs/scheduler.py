from apscheduler.schedulers.background import BackgroundScheduler
from app.services.subscription_automation_service import process_subscriptions
from app.utils.logging import get_logger

logger = get_logger("scheduler")

scheduler = BackgroundScheduler()

# Schedule the daily job at midnight UTC
def start_scheduler():
    scheduler.add_job(process_subscriptions, 'cron', hour=0, minute=0)
    scheduler.start()
    logger.info("Subscription automation scheduler started.")

# Example usage: Call start_scheduler() from your app entrypoint (run.py)
