from src.database import db
from datetime import datetime

class UnitEntity(db.Model):
    """Departamento del edificio (201, 301, 303, 304...)"""
    __tablename__ = 'units'

    unit_id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False, unique=True)  # '201', '301'
    description = db.Column(db.String(200), nullable=True)
    floor = db.Column(db.Integer, nullable=True)
    is_occupied = db.Column(db.Boolean, default=False)
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'unit_id': self.unit_id,
            'code': self.code,
            'description': self.description,
            'floor': self.floor,
            'is_occupied': self.is_occupied,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# DTO Class for Unit
class Unit():
    def __init__(self, unit_id, code, description=None, floor=None, is_occupied=False,
                 enabled=True, created_at=None, updated_at=None) -> None:
        self.unit_id = unit_id
        self.code = code
        self.description = description
        self.floor = floor
        self.is_occupied = is_occupied
        self.enabled = enabled
        self.created_at = created_at
        self.updated_at = updated_at

    def to_json(self):
        return {
            'unit_id': self.unit_id,
            'code': self.code,
            'description': self.description,
            'floor': self.floor,
            'is_occupied': self.is_occupied,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
