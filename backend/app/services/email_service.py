import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
from app.utils.logging import get_logger

logger = get_logger("email_service")

SMTP_HOST = 'smtp.example.com'
SMTP_PORT = 587
SMTP_USER = 'noreply@example.com'
SMTP_PASS = 'yourpassword'

TEMPLATES = {
    'trial_expiry': """Hi {{ name }},<br>Your trial will expire in 3 days. Please upgrade to continue using the platform.""",
    'payment_failed': """Hi {{ name }},<br>Your recent payment failed. Please update your payment method.""",
    'subscription_activated': """Hi {{ name }},<br>Your subscription is now active. Thank you!""",
    'invoice_generated': """Hi {{ name }},<br>Your invoice has been generated. Please find the details in your dashboard."""
}

def send_email(to_email, subject, template_name, context):
    template = Template(TEMPLATES[template_name])
    html = template.render(**context)
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html, 'html'))
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
        logger.info(f"Email sent to {to_email} [{template_name}]")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
