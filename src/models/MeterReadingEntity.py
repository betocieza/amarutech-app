from src.database import db
from datetime import datetime

class MeterReadingEntity(db.Model):
    """Lectura de un medidor en un periodo. El consumo se deriva de las lecturas."""
    __tablename__ = 'meter_readings'
    __table_args__ = (
        db.UniqueConstraint('meter_id', 'period', name='uq_meter_reading_meter_period'),
    )

    reading_id = db.Column(db.Integer, primary_key=True)
    meter_id = db.Column(db.Integer, db.ForeignKey('meters.meter_id'), nullable=False)
    period = db.Column(db.String(7), nullable=False)            # 'YYYY-MM'
    previous_date = db.Column(db.Date, nullable=True)
    current_date = db.Column(db.Date, nullable=True)
    previous_reading = db.Column(db.Numeric(12, 2), nullable=False)
    current_reading = db.Column(db.Numeric(12, 2), nullable=False)
    consumption = db.Column(db.Numeric(12, 2), nullable=False)  # current - previous (KW)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    meter = db.relationship('MeterEntity', backref='readings')

    def to_dict(self):
        return {
            'reading_id': self.reading_id,
            'meter_id': self.meter_id,
            'meter_code': self.meter.code if self.meter else None,
            'unit_id': self.meter.unit_id if self.meter else None,
            'period': self.period,
            'previous_date': self.previous_date.isoformat() if self.previous_date else None,
            'current_date': self.current_date.isoformat() if self.current_date else None,
            'previous_reading': float(self.previous_reading) if self.previous_reading is not None else None,
            'current_reading': float(self.current_reading) if self.current_reading is not None else None,
            'consumption': float(self.consumption) if self.consumption is not None else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# DTO Class for MeterReading
class MeterReading():
    def __init__(self, reading_id, meter_id, period, previous_reading, current_reading,
                 consumption=None, previous_date=None, current_date=None, notes=None,
                 created_at=None, updated_at=None) -> None:
        self.reading_id = reading_id
        self.meter_id = meter_id
        self.period = period
        self.previous_reading = previous_reading
        self.current_reading = current_reading
        self.consumption = consumption
        self.previous_date = previous_date
        self.current_date = current_date
        self.notes = notes
        self.created_at = created_at
        self.updated_at = updated_at

    def to_json(self):
        return {
            'reading_id': self.reading_id,
            'meter_id': self.meter_id,
            'period': self.period,
            'previous_date': self.previous_date.isoformat() if hasattr(self.previous_date, 'isoformat') else self.previous_date,
            'current_date': self.current_date.isoformat() if hasattr(self.current_date, 'isoformat') else self.current_date,
            'previous_reading': float(self.previous_reading) if self.previous_reading is not None else None,
            'current_reading': float(self.current_reading) if self.current_reading is not None else None,
            'consumption': float(self.consumption) if self.consumption is not None else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
