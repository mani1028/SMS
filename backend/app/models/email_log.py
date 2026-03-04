from app.extensions import db
from datetime import datetime

class EmailLog(db.Model):
    __tablename__ = 'email_logs'
    id = db.Column(db.Integer, primary_key=True)
    to_email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    template_name = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<EmailLog {self.to_email} {self.subject} {self.status}>'
