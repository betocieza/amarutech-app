from src.database import db
from datetime import datetime

# Tipos de servicio soportados
SERVICE_ELECTRICITY = 'luz'
SERVICE_WATER = 'agua'
SERVICE_TYPES = (SERVICE_ELECTRICITY, SERVICE_WATER)

class UtilityBillEntity(db.Model):
    """Recibo global del edificio emitido por la empresa de servicios.

    De aqui sale la tarifa que se aplica a cada unidad:
      - luz:  unit_price = total_amount / total_units  (S/ por KW)
      - agua: unit_price = total_amount / total_units  (S/ por persona)
    """
    __tablename__ = 'utility_bills'
    __table_args__ = (
        db.UniqueConstraint('service_type', 'period', name='uq_utility_bill_service_period'),
    )

    bill_id = db.Column(db.Integer, primary_key=True)
    service_type = db.Column(db.String(20), nullable=False)   # 'luz' | 'agua'
    period = db.Column(db.String(7), nullable=False)          # 'YYYY-MM'
    period_start = db.Column(db.Date, nullable=True)
    period_end = db.Column(db.Date, nullable=True)
    total_amount = db.Column(db.Numeric(12, 4), nullable=False)   # total S/ del recibo
    total_units = db.Column(db.Numeric(12, 4), nullable=False)    # total KW o total personas
    unit_price = db.Column(db.Numeric(12, 8), nullable=False)     # S/ por KW o por persona
    due_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'bill_id': self.bill_id,
            'service_type': self.service_type,
            'period': self.period,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'total_amount': float(self.total_amount) if self.total_amount is not None else None,
            'total_units': float(self.total_units) if self.total_units is not None else None,
            'unit_price': float(self.unit_price) if self.unit_price is not None else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# DTO Class for UtilityBill
class UtilityBill():
    def __init__(self, bill_id, service_type, period, total_amount, total_units,
                 unit_price=None, period_start=None, period_end=None, due_date=None,
                 notes=None, created_at=None, updated_at=None) -> None:
        self.bill_id = bill_id
        self.service_type = service_type
        self.period = period
        self.total_amount = total_amount
        self.total_units = total_units
        self.unit_price = unit_price
        self.period_start = period_start
        self.period_end = period_end
        self.due_date = due_date
        self.notes = notes
        self.created_at = created_at
        self.updated_at = updated_at

    def to_json(self):
        return {
            'bill_id': self.bill_id,
            'service_type': self.service_type,
            'period': self.period,
            'period_start': self.period_start.isoformat() if hasattr(self.period_start, 'isoformat') else self.period_start,
            'period_end': self.period_end.isoformat() if hasattr(self.period_end, 'isoformat') else self.period_end,
            'total_amount': float(self.total_amount) if self.total_amount is not None else None,
            'total_units': float(self.total_units) if self.total_units is not None else None,
            'unit_price': float(self.unit_price) if self.unit_price is not None else None,
            'due_date': self.due_date.isoformat() if hasattr(self.due_date, 'isoformat') else self.due_date,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
