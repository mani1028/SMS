from app.extensions import db
from datetime import datetime

class WebhookLog(db.Model):
    __tablename__ = 'webhook_logs'
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(100), nullable=False, index=True)
    payload = db.Column(db.Text, nullable=False)
    signature = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<WebhookLog {self.event_type} {self.created_at}>'
