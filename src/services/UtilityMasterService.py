import traceback
from datetime import datetime, date
from decimal import Decimal

# SQLAlchemy
from src.database import db
from src.models.UnitEntity import UnitEntity
from src.models.TenantEntity import TenantEntity
from src.models.MeterEntity import MeterEntity
from src.models.MeterReadingEntity import MeterReadingEntity
from src.models.UtilityBillEntity import UtilityBillEntity
# Logger
from src.utils.Logger import Logger


def parse_date(value):
    """Convierte 'YYYY-MM-DD' a date. Acepta None y objetos date."""
    if value is None or value == '':
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return datetime.strptime(str(value)[:10], '%Y-%m-%d').date()
    except ValueError:
        return None


class UtilityMasterService():
    """ABM de los maestros del modulo de recibos: unidades, inquilinos,
    medidores, lecturas y recibos globales."""

    # ------------------------------------------------------------------
    # Unidades
    # ------------------------------------------------------------------

    @classmethod
    def get_units(cls, enabled_only=True):
        try:
            query = UnitEntity.query
            if enabled_only:
                query = query.filter_by(enabled=True)
            return [u.to_dict() for u in query.order_by(UnitEntity.code).all()]
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return []

    @classmethod
    def get_unit(cls, unit_id):
        try:
            unit = UnitEntity.query.get(unit_id)
            return unit.to_dict() if unit else None
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None

    @classmethod
    def save_unit(cls, data, unit_id=None):
        try:
            if unit_id:
                unit = UnitEntity.query.get(unit_id)
                if not unit:
                    return None
            else:
                code = str(data.get('code', '')).strip()
                if not code:
                    return None
                if UnitEntity.query.filter_by(code=code).first():
                    return None
                unit = UnitEntity(code=code)
                db.session.add(unit)

            if 'code' in data and data['code']:
                unit.code = str(data['code']).strip()
            if 'description' in data:
                unit.description = data['description']
            if 'floor' in data:
                unit.floor = data['floor']
            if 'is_occupied' in data:
                unit.is_occupied = bool(data['is_occupied'])
            if 'enabled' in data:
                unit.enabled = bool(data['enabled'])

            db.session.commit()
            return unit.to_dict()
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None

    @classmethod
    def delete_unit(cls, unit_id):
        """Deshabilita la unidad. No se borra fisicamente para no perder el
        historico de cargos y lecturas asociados."""
        try:
            unit = UnitEntity.query.get(unit_id)
            if not unit:
                return False
            unit.enabled = False
            db.session.commit()
            return True
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return False

    # ------------------------------------------------------------------
    # Inquilinos
    # ------------------------------------------------------------------

    @classmethod
    def get_tenants(cls, unit_id=None, active_only=False):
        try:
            query = TenantEntity.query
            if unit_id:
                query = query.filter_by(unit_id=unit_id)
            if active_only:
                query = query.filter(TenantEntity.enabled.is_(True),
                                     TenantEntity.end_date.is_(None))
            tenants = query.order_by(TenantEntity.start_date.desc()).all()
            return [t.to_dict() for t in tenants]
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return []

    @classmethod
    def get_tenant(cls, tenant_id):
        try:
            tenant = TenantEntity.query.get(tenant_id)
            return tenant.to_dict() if tenant else None
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None

    @classmethod
    def save_tenant(cls, data, tenant_id=None):
        try:
            if tenant_id:
                tenant = TenantEntity.query.get(tenant_id)
                if not tenant:
                    return None
            else:
                unit_id = data.get('unit_id')
                full_name = str(data.get('full_name', '')).strip()
                start_date = parse_date(data.get('start_date'))
                if not unit_id or not full_name or not start_date:
                    return None
                if not UnitEntity.query.get(unit_id):
                    return None
                tenant = TenantEntity(unit_id=unit_id, full_name=full_name,
                                      start_date=start_date)
                db.session.add(tenant)

            for field in ('full_name', 'document_number', 'phone', 'email'):
                if field in data:
                    tenant.__setattr__(field, data[field])
            if 'unit_id' in data and data['unit_id']:
                tenant.unit_id = data['unit_id']
            if 'people_count' in data:
                tenant.people_count = data['people_count']
            if 'internet_fee' in data and data['internet_fee'] is not None:
                tenant.internet_fee = Decimal(str(data['internet_fee']))
            # Vacio o null limpia la tarifa plana y devuelve al inquilino al
            # prorrateo por personas.
            if 'water_flat_fee' in data:
                raw = data['water_flat_fee']
                if raw is None or str(raw).strip() == '':
                    tenant.water_flat_fee = None
                else:
                    tenant.water_flat_fee = Decimal(str(raw))
            if 'start_date' in data and data['start_date']:
                tenant.start_date = parse_date(data['start_date'])
            if 'end_date' in data:
                tenant.end_date = parse_date(data['end_date'])
            if 'enabled' in data:
                tenant.enabled = bool(data['enabled'])

            db.session.commit()
            return tenant.to_dict()
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None

    @classmethod
    def delete_tenant(cls, tenant_id):
        try:
            tenant = TenantEntity.query.get(tenant_id)
            if not tenant:
                return False
            tenant.enabled = False
            db.session.commit()
            return True
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return False

    # ------------------------------------------------------------------
    # Medidores
    # ------------------------------------------------------------------

    @classmethod
    def get_meters(cls, unit_id=None, active_only=False):
        try:
            query = MeterEntity.query
            if unit_id:
                query = query.filter_by(unit_id=unit_id)
            if active_only:
                query = query.filter(MeterEntity.enabled.is_(True),
                                     MeterEntity.valid_to.is_(None))
            meters = query.order_by(MeterEntity.code, MeterEntity.valid_from).all()
            return [m.to_dict() for m in meters]
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return []

    @classmethod
    def get_meter(cls, meter_id):
        try:
            meter = MeterEntity.query.get(meter_id)
            return meter.to_dict() if meter else None
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None

    @classmethod
    def save_meter(cls, data, meter_id=None):
        try:
            if meter_id:
                meter = MeterEntity.query.get(meter_id)
                if not meter:
                    return None
            else:
                unit_id = data.get('unit_id')
                code = str(data.get('code', '')).strip()
                valid_from = parse_date(data.get('valid_from'))
                if not unit_id or not code or not valid_from:
                    return None
                if not UnitEntity.query.get(unit_id):
                    return None
                meter = MeterEntity(unit_id=unit_id, code=code, valid_from=valid_from)
                db.session.add(meter)

            if 'unit_id' in data and data['unit_id']:
                meter.unit_id = data['unit_id']
            if 'code' in data and data['code']:
                meter.code = str(data['code']).strip()
            if 'valid_from' in data and data['valid_from']:
                meter.valid_from = parse_date(data['valid_from'])
            if 'valid_to' in data:
                meter.valid_to = parse_date(data['valid_to'])
            if 'enabled' in data:
                meter.enabled = bool(data['enabled'])

            # La vigencia no puede terminar antes de empezar
            if meter.valid_to and meter.valid_from and meter.valid_to < meter.valid_from:
                db.session.rollback()
                return None

            db.session.commit()
            return meter.to_dict()
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None

    @classmethod
    def replace_meter(cls, unit_id, old_meter_id, new_code, change_date):
        """Cierra la vigencia del medidor actual y abre la del nuevo.

        Es el caso del 303: el medidor 301 dejo de usarse el 07/05/2026 y desde
        esa fecha consume por el 303. Ambos quedan vigentes en su tramo, asi que
        el consumo del periodo suma los dos.
        """
        try:
            change_date = parse_date(change_date)
            if not change_date or not new_code:
                return None

            old_meter = MeterEntity.query.get(old_meter_id)
            if not old_meter or old_meter.unit_id != unit_id:
                return None

            old_meter.valid_to = change_date
            new_meter = MeterEntity(unit_id=unit_id, code=str(new_code).strip(),
                                    valid_from=change_date, enabled=True)
            db.session.add(new_meter)
            db.session.commit()
            return {'previous': old_meter.to_dict(), 'current': new_meter.to_dict()}
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None

    @classmethod
    def delete_meter(cls, meter_id):
        try:
            meter = MeterEntity.query.get(meter_id)
            if not meter:
                return False
            meter.enabled = False
            db.session.commit()
            return True
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return False

    # ------------------------------------------------------------------
    # Lecturas
    # ------------------------------------------------------------------

    @classmethod
    def get_readings(cls, period=None, meter_id=None, unit_id=None):
        try:
            query = MeterReadingEntity.query.join(MeterEntity)
            if period:
                query = query.filter(MeterReadingEntity.period == period)
            if meter_id:
                query = query.filter(MeterReadingEntity.meter_id == meter_id)
            if unit_id:
                query = query.filter(MeterEntity.unit_id == unit_id)
            readings = query.order_by(MeterReadingEntity.period.desc(),
                                      MeterEntity.code).all()
            return [r.to_dict() for r in readings]
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return []

    @classmethod
    def get_last_reading(cls, meter_id, before_period=None):
        """Ultima lectura del medidor, para precargar la lectura anterior."""
        try:
            query = MeterReadingEntity.query.filter_by(meter_id=meter_id)
            if before_period:
                query = query.filter(MeterReadingEntity.period < before_period)
            reading = query.order_by(MeterReadingEntity.period.desc()).first()
            return reading.to_dict() if reading else None
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None

    @classmethod
    def save_reading(cls, data, reading_id=None):
        """Registra una lectura. El consumo se calcula solo.

        Si no viene la lectura anterior, se toma la ultima registrada del
        medidor, que es como se encadenan los periodos en el Excel.
        """
        try:
            # Los valores se resuelven y validan ANTES de tocar la sesion: una
            # entidad a medio llenar en la sesion se insertaria incompleta en el
            # primer autoflush que dispare cualquier consulta posterior.
            reading = None
            if reading_id:
                reading = MeterReadingEntity.query.get(reading_id)
                if not reading:
                    return None
                meter_id = data.get('meter_id') or reading.meter_id
                period = data.get('period') or reading.period
            else:
                meter_id = data.get('meter_id')
                period = data.get('period')
                if not meter_id or not period:
                    return None
                if not MeterEntity.query.get(meter_id):
                    return None
                # Una lectura por medidor y periodo
                reading = MeterReadingEntity.query.filter_by(
                    meter_id=meter_id, period=period).first()

            previous_date = (parse_date(data['previous_date']) if 'previous_date' in data
                             else (reading.previous_date if reading else None))
            current_date = (parse_date(data['current_date']) if 'current_date' in data
                            else (reading.current_date if reading else None))

            if data.get('previous_reading') is not None:
                previous_reading = Decimal(str(data['previous_reading']))
            elif reading is not None and reading.previous_reading is not None:
                previous_reading = reading.previous_reading
            else:
                last = cls.get_last_reading(meter_id, period)
                previous_reading = (Decimal(str(last['current_reading']))
                                    if last else Decimal('0'))
                if last and not previous_date:
                    previous_date = parse_date(last['current_date'])

            if data.get('current_reading') is not None:
                current_reading = Decimal(str(data['current_reading']))
            elif reading is not None:
                current_reading = reading.current_reading
            else:
                current_reading = None

            if current_reading is None:
                return None

            # Un medidor no retrocede: si la lectura actual es menor, hay un
            # error de digitacion o el medidor se reinicio. No se guarda.
            if current_reading < previous_reading:
                return None

            if reading is None:
                reading = MeterReadingEntity(meter_id=meter_id, period=period)
                db.session.add(reading)

            reading.meter_id = meter_id
            reading.period = period
            reading.previous_date = previous_date
            reading.current_date = current_date
            reading.previous_reading = previous_reading
            reading.current_reading = current_reading
            reading.consumption = current_reading - previous_reading
            if 'notes' in data:
                reading.notes = data['notes']

            db.session.commit()
            return reading.to_dict()
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None

    @classmethod
    def delete_reading(cls, reading_id):
        try:
            reading = MeterReadingEntity.query.get(reading_id)
            if not reading:
                return False
            db.session.delete(reading)
            db.session.commit()
            return True
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return False

    @staticmethod
    def _next_cycle_date(previous_date):
        """Mismo dia del mes siguiente, ajustado si ese dia no existe."""
        year = previous_date.year + (1 if previous_date.month == 12 else 0)
        month = 1 if previous_date.month == 12 else previous_date.month + 1
        day = previous_date.day
        while day > 28:
            try:
                return date(year, month, day)
            except ValueError:
                day -= 1
        return date(year, month, day)

    @classmethod
    def get_reading_sheet(cls, period):
        """Planilla de lecturas del periodo: un renglon por medidor vigente de
        las unidades ocupadas, con la lectura anterior ya precargada.

        Se excluyen los departamentos sin inquilino en el periodo y los medidores
        cuya vigencia ya cerro antes de que empiece el mes: un medidor
        reemplazado no debe seguir pidiendo lectura.
        """
        try:
            # Import local: UtilityBillingService importa este modulo, asi que
            # a nivel de modulo seria circular.
            from src.services.UtilityBillingService import (UtilityBillingService,
                                                            period_bounds)
            month_start, month_end = period_bounds(period)

            occupied_ids = [u.unit_id for u in
                            UtilityBillingService.get_occupied_units(period)]
            if not occupied_ids:
                return []

            meters = (MeterEntity.query
                      .join(UnitEntity)
                      .filter(MeterEntity.enabled.is_(True),
                              MeterEntity.unit_id.in_(occupied_ids),
                              MeterEntity.valid_from <= month_end,
                              db.or_(MeterEntity.valid_to.is_(None),
                                     MeterEntity.valid_to >= month_start))
                      .order_by(UnitEntity.code, MeterEntity.code).all())
            rows = []
            for meter in meters:
                current = MeterReadingEntity.query.filter_by(
                    meter_id=meter.meter_id, period=period).first()
                last = cls.get_last_reading(meter.meter_id, period)
                # Fecha de la toma anterior: es el inicio del ciclo que se va a
                # facturar. El ciclo va de toma a toma segun el dia de ingreso del
                # inquilino, asi que no arranca el 1 del mes.
                if current and current.previous_date:
                    previous_date = current.previous_date
                elif last and last.get('current_date'):
                    previous_date = parse_date(last['current_date'])
                else:
                    previous_date = None

                # Fecha sugerida para la toma: el mismo dia del mes siguiente al
                # de la toma anterior, que es como se vienen encadenando.
                suggested = None
                if previous_date:
                    suggested = cls._next_cycle_date(previous_date)

                rows.append({
                    'meter_id': meter.meter_id,
                    'meter_code': meter.code,
                    'unit_id': meter.unit_id,
                    'unit_code': meter.unit.code if meter.unit else None,
                    'period': period,
                    'previous_date': previous_date.isoformat() if previous_date else None,
                    'current_date': (current.current_date.isoformat()
                                     if current and current.current_date
                                     else (suggested.isoformat() if suggested else None)),
                    'previous_reading': (float(current.previous_reading) if current
                                         else (last['current_reading'] if last else 0)),
                    'current_reading': float(current.current_reading) if current else None,
                    'consumption': float(current.consumption) if current else None,
                    'reading_id': current.reading_id if current else None,
                    'registered': current is not None,
                })
            return rows
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return []

    # ------------------------------------------------------------------
    # Recibos globales
    # ------------------------------------------------------------------

    @classmethod
    def get_bills(cls, period=None, service_type=None):
        try:
            query = UtilityBillEntity.query
            if period:
                query = query.filter_by(period=period)
            if service_type:
                query = query.filter_by(service_type=service_type)
            bills = query.order_by(UtilityBillEntity.period.desc(),
                                   UtilityBillEntity.service_type).all()
            return [b.to_dict() for b in bills]
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return []

    @classmethod
    def delete_bill(cls, bill_id):
        try:
            bill = UtilityBillEntity.query.get(bill_id)
            if not bill:
                return False
            db.session.delete(bill)
            db.session.commit()
            return True
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return False
