from src.database import db
from datetime import datetime

# Estados del cargo
STATUS_PENDING = 'pendiente'
STATUS_PARTIAL = 'parcial'
STATUS_PAID = 'pagado'
CHARGE_STATUSES = (STATUS_PENDING, STATUS_PARTIAL, STATUS_PAID)

class UnitChargeEntity(db.Model):
    """Cobro mensual consolidado de servicios para una unidad.

    Reemplaza cada bloque 'RECIBO DE LUZ / AGUA / INTERNET' del Excel.
    total_amount = electricity + water + internet - previous_credit
    """
    __tablename__ = 'unit_charges'
    __table_args__ = (
        db.UniqueConstraint('unit_id', 'period', name='uq_unit_charge_unit_period'),
    )

    charge_id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.unit_id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.tenant_id'), nullable=True)
    period = db.Column(db.String(7), nullable=False)          # 'YYYY-MM'
    period_start = db.Column(db.Date, nullable=True)
    period_end = db.Column(db.Date, nullable=True)

    # Luz
    electricity_consumption = db.Column(db.Numeric(12, 2), default=0)  # KW del periodo
    electricity_price = db.Column(db.Numeric(12, 8), default=0)        # S/ por KW aplicado
    electricity_amount = db.Column(db.Numeric(12, 4), default=0)

    # Agua
    water_people = db.Column(db.Integer, default=0)
    water_price = db.Column(db.Numeric(12, 8), default=0)              # S/ por persona
    water_amount = db.Column(db.Numeric(12, 4), default=0)

    # Internet
    internet_amount = db.Column(db.Numeric(12, 4), default=0)

    # Saldos
    previous_credit = db.Column(db.Numeric(12, 4), default=0)  # saldo a favor arrastrado
    total_amount = db.Column(db.Numeric(12, 4), default=0)     # neto a pagar
    paid_amount = db.Column(db.Numeric(12, 4), default=0)
    credit_balance = db.Column(db.Numeric(12, 4), default=0)   # saldo a favor generado
    status = db.Column(db.String(20), default=STATUS_PENDING)

    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    unit = db.relationship('UnitEntity', backref='charges')
    tenant = db.relationship('TenantEntity', backref='charges')

    def to_dict(self):
        return {
            'charge_id': self.charge_id,
            'unit_id': self.unit_id,
            'unit_code': self.unit.code if self.unit else None,
            'tenant_id': self.tenant_id,
            'tenant_name': self.tenant.full_name if self.tenant else None,
            'period': self.period,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'electricity_consumption': float(self.electricity_consumption or 0),
            'electricity_price': float(self.electricity_price or 0),
            'electricity_amount': float(self.electricity_amount or 0),
            'water_people': self.water_people,
            'water_price': float(self.water_price or 0),
            'water_amount': float(self.water_amount or 0),
            'internet_amount': float(self.internet_amount or 0),
            'previous_credit': float(self.previous_credit or 0),
            'total_amount': float(self.total_amount or 0),
            'paid_amount': float(self.paid_amount or 0),
            'credit_balance': float(self.credit_balance or 0),
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# DTO Class for UnitCharge
class UnitCharge():
    def __init__(self, charge_id, unit_id, period, tenant_id=None, period_start=None,
                 period_end=None, electricity_consumption=0, electricity_price=0,
                 electricity_amount=0, water_people=0, water_price=0, water_amount=0,
                 internet_amount=0, previous_credit=0, total_amount=0, paid_amount=0,
                 credit_balance=0, status=STATUS_PENDING, notes=None,
                 created_at=None, updated_at=None) -> None:
        self.charge_id = charge_id
        self.unit_id = unit_id
        self.tenant_id = tenant_id
        self.period = period
        self.period_start = period_start
        self.period_end = period_end
        self.electricity_consumption = electricity_consumption
        self.electricity_price = electricity_price
        self.electricity_amount = electricity_amount
        self.water_people = water_people
        self.water_price = water_price
        self.water_amount = water_amount
        self.internet_amount = internet_amount
        self.previous_credit = previous_credit
        self.total_amount = total_amount
        self.paid_amount = paid_amount
        self.credit_balance = credit_balance
        self.status = status
        self.notes = notes
        self.created_at = created_at
        self.updated_at = updated_at

    def to_json(self):
        return {
            'charge_id': self.charge_id,
            'unit_id': self.unit_id,
            'tenant_id': self.tenant_id,
            'period': self.period,
            'period_start': self.period_start.isoformat() if hasattr(self.period_start, 'isoformat') else self.period_start,
            'period_end': self.period_end.isoformat() if hasattr(self.period_end, 'isoformat') else self.period_end,
            'electricity_consumption': float(self.electricity_consumption or 0),
            'electricity_price': float(self.electricity_price or 0),
            'electricity_amount': float(self.electricity_amount or 0),
            'water_people': self.water_people,
            'water_price': float(self.water_price or 0),
            'water_amount': float(self.water_amount or 0),
            'internet_amount': float(self.internet_amount or 0),
            'previous_credit': float(self.previous_credit or 0),
            'total_amount': float(self.total_amount or 0),
            'paid_amount': float(self.paid_amount or 0),
            'credit_balance': float(self.credit_balance or 0),
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
