from app.extensions import db
from datetime import datetime
import secrets

class ApiKey(db.Model):
    __tablename__ = 'api_keys'
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, nullable=False)
    key = db.Column(db.String(64), unique=True, nullable=False, default=lambda: secrets.token_hex(32))
    is_active = db.Column(db.Boolean, default=True)
    usage_count = db.Column(db.Integer, default=0)
    daily_limit = db.Column(db.Integer, default=10000)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ApiKey {self.key[:8]}... for school {self.school_id}>'
