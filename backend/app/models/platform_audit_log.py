from app.extensions import db
from datetime import datetime

class PlatformAuditLog(db.Model):
    __tablename__ = 'platform_audit_log'
    id = db.Column(db.Integer, primary_key=True)
    action_type = db.Column(db.String(100), nullable=False, index=True)
    actor_id = db.Column(db.Integer)
    actor_role = db.Column(db.String(50))
    school_id = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<PlatformAuditLog {self.action_type} {self.created_at}>'
