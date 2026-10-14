from src.database import db
from datetime import datetime

class PaymentEntity(db.Model):
    """Pago recibido contra un cargo mensual. Si excede el total genera saldo a favor."""
    __tablename__ = 'payments'

    payment_id = db.Column(db.Integer, primary_key=True)
    charge_id = db.Column(db.Integer, db.ForeignKey('unit_charges.charge_id'), nullable=False)
    amount = db.Column(db.Numeric(12, 4), nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    method = db.Column(db.String(50), nullable=True)      # efectivo, yape, transferencia
    reference = db.Column(db.String(100), nullable=True)  # nro de operacion
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    charge = db.relationship('UnitChargeEntity', backref='payments')

    def to_dict(self):
        return {
            'payment_id': self.payment_id,
            'charge_id': self.charge_id,
            'unit_code': self.charge.unit.code if self.charge and self.charge.unit else None,
            'period': self.charge.period if self.charge else None,
            'amount': float(self.amount) if self.amount is not None else None,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'method': self.method,
            'reference': self.reference,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# DTO Class for Payment
class Payment():
    def __init__(self, payment_id, charge_id, amount, payment_date, method=None,
                 reference=None, notes=None, created_at=None, updated_at=None) -> None:
        self.payment_id = payment_id
        self.charge_id = charge_id
        self.amount = amount
        self.payment_date = payment_date
        self.method = method
        self.reference = reference
        self.notes = notes
        self.created_at = created_at
        self.updated_at = updated_at

    def to_json(self):
        return {
            'payment_id': self.payment_id,
            'charge_id': self.charge_id,
            'amount': float(self.amount) if self.amount is not None else None,
            'payment_date': self.payment_date.isoformat() if hasattr(self.payment_date, 'isoformat') else self.payment_date,
            'method': self.method,
            'reference': self.reference,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
