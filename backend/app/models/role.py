from app.models.base import BaseModel
from app.extensions import db


role_permission_table = db.Table(
    'role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
)


class Role(BaseModel):
    """Role model - Multi-tenant"""
    __tablename__ = 'roles'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    permissions = db.relationship(
        'Permission',
        secondary=role_permission_table,
        backref=db.backref('roles', lazy='dynamic')
    )
    
    # Unique constraint on name per school
    __table_args__ = (db.UniqueConstraint('school_id', 'name', name='uq_school_role'),)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'name': self.name,
            'description': self.description,
            'permissions': [p.to_dict() for p in self.permissions]
        })
        return data
    
    def __repr__(self):
        return f'<Role {self.name}>'
