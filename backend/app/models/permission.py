from app.models.base import BaseModel
from app.extensions import db


class Permission(BaseModel):
    """Permission model - Global (not multi-tenant)"""
    __tablename__ = 'permissions'
    
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'name': self.name,
            'description': self.description
        })
        return data
    
    def __repr__(self):
        return f'<Permission {self.name}>'
