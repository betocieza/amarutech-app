from src.database import db
from datetime import datetime

class TenantEntity(db.Model):
    """Inquilino de un departamento"""
    __tablename__ = 'tenants'

    tenant_id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.unit_id'), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    document_number = db.Column(db.String(30), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    people_count = db.Column(db.Integer, default=1)          # para prorrateo de agua
    internet_fee = db.Column(db.Numeric(10, 2), default=0)   # monto fijo mensual de internet
    # Tarifa plana de agua pactada con el inquilino. NULL = se prorratea por
    # personas como al resto; un monto aqui reemplaza ese calculo.
    water_flat_fee = db.Column(db.Numeric(10, 2), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)             # NULL = vigente
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    unit = db.relationship('UnitEntity', backref='tenants')

    def to_dict(self):
        return {
            'tenant_id': self.tenant_id,
            'unit_id': self.unit_id,
            'unit_code': self.unit.code if self.unit else None,
            'full_name': self.full_name,
            'document_number': self.document_number,
            'phone': self.phone,
            'email': self.email,
            'people_count': self.people_count,
            'internet_fee': float(self.internet_fee) if self.internet_fee is not None else 0,
            'water_flat_fee': float(self.water_flat_fee) if self.water_flat_fee is not None else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# DTO Class for Tenant
class Tenant():
    def __init__(self, tenant_id, unit_id, full_name, document_number=None, phone=None,
                 email=None, people_count=1, internet_fee=0, water_flat_fee=None,
                 start_date=None, end_date=None,
                 enabled=True, created_at=None, updated_at=None) -> None:
        self.tenant_id = tenant_id
        self.unit_id = unit_id
        self.full_name = full_name
        self.document_number = document_number
        self.phone = phone
        self.email = email
        self.people_count = people_count
        self.internet_fee = internet_fee
        self.water_flat_fee = water_flat_fee
        self.start_date = start_date
        self.end_date = end_date
        self.enabled = enabled
        self.created_at = created_at
        self.updated_at = updated_at

    def to_json(self):
        return {
            'tenant_id': self.tenant_id,
            'unit_id': self.unit_id,
            'full_name': self.full_name,
            'document_number': self.document_number,
            'phone': self.phone,
            'email': self.email,
            'people_count': self.people_count,
            'internet_fee': float(self.internet_fee) if self.internet_fee is not None else 0,
            'water_flat_fee': float(self.water_flat_fee) if self.water_flat_fee is not None else None,
            'start_date': self.start_date.isoformat() if hasattr(self.start_date, 'isoformat') else self.start_date,
            'end_date': self.end_date.isoformat() if hasattr(self.end_date, 'isoformat') else self.end_date,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
