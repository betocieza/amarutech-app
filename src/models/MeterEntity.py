from src.database import db
from datetime import datetime

class MeterEntity(db.Model):
    """Medidor de luz asignado a una unidad durante un rango de vigencia.

    Una unidad puede tener varios medidores a lo largo del tiempo (ej: el 303
    consumio por el medidor 301 hasta el 07/05/2026 y por el 303 desde esa fecha).
    El rango [valid_from, valid_to] permite calcular el consumo de un periodo
    sumando todos los medidores vigentes en el.
    """
    __tablename__ = 'meters'

    meter_id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.unit_id'), nullable=False)
    code = db.Column(db.String(30), nullable=False)   # '201', '301', '303'
    valid_from = db.Column(db.Date, nullable=False)
    valid_to = db.Column(db.Date, nullable=True)      # NULL = vigente
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    unit = db.relationship('UnitEntity', backref='meters')

    def to_dict(self):
        return {
            'meter_id': self.meter_id,
            'unit_id': self.unit_id,
            'unit_code': self.unit.code if self.unit else None,
            'code': self.code,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_to': self.valid_to.isoformat() if self.valid_to else None,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# DTO Class for Meter
class Meter():
    def __init__(self, meter_id, unit_id, code, valid_from=None, valid_to=None,
                 enabled=True, created_at=None, updated_at=None) -> None:
        self.meter_id = meter_id
        self.unit_id = unit_id
        self.code = code
        self.valid_from = valid_from
        self.valid_to = valid_to
        self.enabled = enabled
        self.created_at = created_at
        self.updated_at = updated_at

    def to_json(self):
        return {
            'meter_id': self.meter_id,
            'unit_id': self.unit_id,
            'code': self.code,
            'valid_from': self.valid_from.isoformat() if hasattr(self.valid_from, 'isoformat') else self.valid_from,
            'valid_to': self.valid_to.isoformat() if hasattr(self.valid_to, 'isoformat') else self.valid_to,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
