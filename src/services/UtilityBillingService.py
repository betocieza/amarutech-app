import traceback
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

# SQLAlchemy
from src.database import db
from src.models.UnitEntity import UnitEntity
from src.models.TenantEntity import TenantEntity
from src.models.MeterEntity import MeterEntity
from src.models.UtilityBillEntity import (UtilityBillEntity, SERVICE_ELECTRICITY,
                                          SERVICE_WATER)
from src.models.MeterReadingEntity import MeterReadingEntity
from src.models.UnitChargeEntity import (UnitChargeEntity, STATUS_PENDING,
                                         STATUS_PARTIAL, STATUS_PAID)
from src.models.PaymentEntity import PaymentEntity
# Logger
from src.utils.Logger import Logger

TWO_PLACES = Decimal('0.01')
ZERO = Decimal('0')


def money(value):
    """Redondea a 2 decimales con redondeo comercial."""
    if value is None:
        return ZERO
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def period_bounds(period):
    """Primer y ultimo dia del periodo 'YYYY-MM'."""
    year, month = int(period[:4]), int(period[5:7])
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return start, end - timedelta(days=1)


def previous_period(period):
    year, month = int(period[:4]), int(period[5:7])
    return '%04d-%02d' % (year - 1, 12) if month == 1 else '%04d-%02d' % (year, month - 1)


class UtilityBillingService():
    """Motor de calculo de los cobros de servicios.

    Reemplaza las formulas que vivian en el Excel:
      - tarifa de luz  = total del recibo global / total KW del edificio
      - tarifa de agua = total del recibo global / total de personas
      - consumo de una unidad = suma de todos sus medidores vigentes en el periodo
      - arrastre automatico del saldo a favor del periodo anterior
      - faltante de areas comunes = recibo global - suma cobrada a las unidades

    El faltante de areas comunes lo asume el propietario: se reporta, nunca se
    reparte entre los departamentos.
    """

    # ------------------------------------------------------------------
    # Tarifas
    # ------------------------------------------------------------------

    @classmethod
    def get_unit_price(cls, service_type, period):
        """Tarifa del periodo segun el recibo global. None si no esta cargado."""
        try:
            bill = UtilityBillEntity.query.filter_by(
                service_type=service_type, period=period).first()
            return bill.unit_price if bill else None
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None

    @classmethod
    def save_bill(cls, service_type, period, total_amount, total_units,
                  period_start=None, period_end=None, due_date=None, notes=None):
        """Registra o actualiza el recibo global y recalcula su tarifa."""
        try:
            total_amount = Decimal(str(total_amount))
            total_units = Decimal(str(total_units))
            if total_units == ZERO:
                return None

            bill = UtilityBillEntity.query.filter_by(
                service_type=service_type, period=period).first()
            if not bill:
                bill = UtilityBillEntity(service_type=service_type, period=period)
                db.session.add(bill)

            bill.total_amount = total_amount
            bill.total_units = total_units
            bill.unit_price = total_amount / total_units
            bill.period_start = period_start
            bill.period_end = period_end
            bill.due_date = due_date
            bill.notes = notes
            db.session.commit()
            return bill.to_dict()
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None

    # ------------------------------------------------------------------
    # Consumo por unidad
    # ------------------------------------------------------------------

    @classmethod
    def get_unit_consumption(cls, unit_id, period):
        """Consumo total en KW de una unidad, sumando todos sus medidores.

        Una unidad puede cambiar de medidor a mitad de periodo (el 303 consumio
        por el medidor 301 hasta el 07/05/2026 y por el 303 desde esa fecha).
        Se suman las lecturas de todos los medidores de la unidad en el periodo.
        """
        try:
            readings = (MeterReadingEntity.query
                        .join(MeterEntity)
                        .filter(MeterEntity.unit_id == unit_id,
                                MeterReadingEntity.period == period)
                        .all())
            total = ZERO
            for r in readings:
                total += r.consumption or ZERO
            return total
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return ZERO

    @classmethod
    def get_unit_cycle(cls, unit_id, period):
        """Fechas reales del ciclo facturado a la unidad en el periodo.

        El ciclo va de toma a toma y arranca el dia que el inquilino ingreso, asi
        que no coincide con el mes calendario: el 304 se lee del 20 al 20 y el 301
        del 4 al 4. Se toma la fecha mas temprana de lectura anterior y la mas
        tardia de lectura actual, de modo que un cambio de medidor a mitad de
        ciclo quede cubierto por completo.

        Devuelve (inicio, fin), con None donde no haya lecturas fechadas.
        """
        try:
            readings = (MeterReadingEntity.query
                        .join(MeterEntity)
                        .filter(MeterEntity.unit_id == unit_id,
                                MeterReadingEntity.period == period)
                        .all())
            starts = [r.previous_date for r in readings if r.previous_date]
            ends = [r.current_date for r in readings if r.current_date]
            return (min(starts) if starts else None,
                    max(ends) if ends else None)
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None, None

    @classmethod
    def get_active_tenant(cls, unit_id, period):
        """Inquilino vigente de la unidad durante el periodo."""
        try:
            start, end = period_bounds(period)
            return (TenantEntity.query
                    .filter(TenantEntity.unit_id == unit_id,
                            TenantEntity.enabled.is_(True),
                            TenantEntity.start_date <= end,
                            db.or_(TenantEntity.end_date.is_(None),
                                   TenantEntity.end_date >= start))
                    .order_by(TenantEntity.start_date.desc())
                    .first())
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None

    @classmethod
    def get_occupied_units(cls, period):
        """Unidades con inquilino vigente durante el periodo.

        Un departamento vacio no genera cobro ni entra en las planillas: el 301
        quedo libre cuando su inquilino paso al 303 y no debe seguir apareciendo
        mes a mes. La ocupacion se deduce de los contratos, no del check manual
        de la unidad, asi aparece y desaparece solo segun las fechas.
        """
        try:
            start, end = period_bounds(period)
            return (UnitEntity.query
                    .join(TenantEntity, TenantEntity.unit_id == UnitEntity.unit_id)
                    .filter(UnitEntity.enabled.is_(True),
                            TenantEntity.enabled.is_(True),
                            TenantEntity.start_date <= end,
                            db.or_(TenantEntity.end_date.is_(None),
                                   TenantEntity.end_date >= start))
                    .order_by(UnitEntity.code)
                    .distinct()
                    .all())
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return []

    @classmethod
    def get_previous_credit(cls, unit_id, period):
        """Saldo a favor que dejo la unidad en el periodo anterior."""
        try:
            prev = UnitChargeEntity.query.filter_by(
                unit_id=unit_id, period=previous_period(period)).first()
            return (prev.credit_balance or ZERO) if prev else ZERO
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return ZERO

    # ------------------------------------------------------------------
    # Generacion de cobros
    # ------------------------------------------------------------------

    @classmethod
    def generate_period(cls, period, commit=True):
        """Genera o actualiza los cobros de todas las unidades del periodo.

        Devuelve un resumen con los cargos generados y el cuadre contra los
        recibos globales. No pisa un cargo que ya tenga pagos registrados.
        """
        try:
            # Limites del mes calendario: solo se usan como respaldo cuando una
            # unidad todavia no tiene lecturas fechadas en el periodo.
            month_start, month_end = period_bounds(period)
            elec_price = cls.get_unit_price(SERVICE_ELECTRICITY, period)
            water_price = cls.get_unit_price(SERVICE_WATER, period)

            warnings = []
            if elec_price is None:
                warnings.append('No hay recibo global de luz cargado para %s' % period)
            if water_price is None:
                warnings.append('No hay recibo global de agua cargado para %s' % period)

            # Solo las unidades con inquilino vigente: un departamento vacio no
            # genera cobro.
            units = cls.get_occupied_units(period)
            charges = []
            skipped = []

            for unit in units:
                charge = UnitChargeEntity.query.filter_by(
                    unit_id=unit.unit_id, period=period).first()

                # Un cargo con pagos ya registrados no se recalcula: cambiar el
                # monto dejaria los pagos descuadrados.
                if charge and (charge.paid_amount or ZERO) > ZERO:
                    skipped.append({'unit_code': unit.code,
                                    'reason': 'tiene pagos registrados'})
                    charges.append(charge)
                    continue

                tenant = cls.get_active_tenant(unit.unit_id, period)
                consumption = cls.get_unit_consumption(unit.unit_id, period)

                # Luz
                e_price = elec_price or ZERO
                e_amount = money(consumption * e_price)

                # Agua: por defecto se prorratea por persona del inquilino
                # vigente. Si tiene tarifa plana pactada, esa reemplaza el
                # calculo: se guarda con personas y tarifa en cero para que el
                # recibo no muestre un prorrateo que no ocurrio.
                # El inquilino con tarifa plana sigue contando en el total de
                # personas del recibo global, asi que la tarifa de los demas no
                # cambia: la diferencia la absorbe el propietario.
                if tenant and tenant.water_flat_fee is not None:
                    people = 0
                    w_price = ZERO
                    w_amount = money(tenant.water_flat_fee)
                else:
                    people = (tenant.people_count or 0) if tenant else 0
                    w_price = water_price or ZERO
                    w_amount = money(Decimal(people) * w_price)

                # Internet: monto fijo pactado con el inquilino
                i_amount = money(tenant.internet_fee) if tenant else ZERO

                credit = cls.get_previous_credit(unit.unit_id, period)
                total = money(e_amount + w_amount + i_amount - credit)

                if not charge:
                    charge = UnitChargeEntity(unit_id=unit.unit_id, period=period)
                    db.session.add(charge)

                # El ciclo sale de las lecturas: va de toma a toma segun la fecha
                # de ingreso de cada inquilino, no del 1 al 30 del mes.
                cycle_start, cycle_end = cls.get_unit_cycle(unit.unit_id, period)

                charge.tenant_id = tenant.tenant_id if tenant else None
                charge.period_start = cycle_start or month_start
                charge.period_end = cycle_end or month_end
                charge.electricity_consumption = consumption
                charge.electricity_price = e_price
                charge.electricity_amount = e_amount
                charge.water_people = people
                charge.water_price = w_price
                charge.water_amount = w_amount
                charge.internet_amount = i_amount
                charge.previous_credit = credit
                charge.total_amount = total
                charge.paid_amount = charge.paid_amount or ZERO
                charge.credit_balance = charge.credit_balance or ZERO
                charge.status = charge.status or STATUS_PENDING
                charges.append(charge)

            # Cobros de unidades que quedaron vacias: se eliminan para que el
            # departamento desaparezca del periodo. Uno con pagos registrados se
            # conserva, porque borrarlo perderia la plata ya cobrada.
            occupied_ids = {u.unit_id for u in units}
            removed = []
            orphans = (UnitChargeEntity.query
                       .filter(UnitChargeEntity.period == period,
                               UnitChargeEntity.unit_id.notin_(occupied_ids))
                       .all()) if occupied_ids else []
            for orphan in orphans:
                code = orphan.unit.code if orphan.unit else str(orphan.unit_id)
                if (orphan.paid_amount or ZERO) > ZERO:
                    skipped.append({'unit_code': code,
                                    'reason': 'sin inquilino pero tiene pagos registrados'})
                    continue
                db.session.delete(orphan)
                removed.append(code)

            if commit:
                db.session.commit()
            else:
                db.session.flush()

            summary = cls.get_period_summary(period)
            summary['warnings'] = warnings
            summary['skipped'] = skipped
            summary['removed'] = removed
            summary['generated'] = len(charges) - len(skipped)
            return summary
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None

    # ------------------------------------------------------------------
    # Resumen y cuadre
    # ------------------------------------------------------------------

    @classmethod
    def get_period_summary(cls, period):
        """Consolidado del periodo: lo que reemplaza la hoja TOTALESXMES.

        Incluye el faltante de areas comunes, que es lo que el Excel no mostraba:
        la diferencia entre el recibo global y lo repartido entre las unidades.
        """
        try:
            charges = (UnitChargeEntity.query
                       .join(UnitEntity)
                       .filter(UnitChargeEntity.period == period)
                       .order_by(UnitEntity.code)
                       .all())

            elec_billed = sum((c.electricity_amount or ZERO for c in charges), ZERO)
            water_billed = sum((c.water_amount or ZERO for c in charges), ZERO)
            # Un cargo con tarifa plana de agua se guarda sin personas. Separarlo
            # evita leer como area comun lo que en realidad es la rebaja pactada
            # con ese inquilino.
            water_flat = sum((c.water_amount or ZERO for c in charges
                              if not c.water_people and (c.water_amount or ZERO) > ZERO), ZERO)
            water_prorated = money(water_billed - water_flat)
            internet_billed = sum((c.internet_amount or ZERO for c in charges), ZERO)
            total_billed = sum((c.total_amount or ZERO for c in charges), ZERO)
            total_paid = sum((c.paid_amount or ZERO for c in charges), ZERO)
            total_kw = sum((c.electricity_consumption or ZERO for c in charges), ZERO)

            elec_bill = UtilityBillEntity.query.filter_by(
                service_type=SERVICE_ELECTRICITY, period=period).first()
            water_bill = UtilityBillEntity.query.filter_by(
                service_type=SERVICE_WATER, period=period).first()

            elec_total = elec_bill.total_amount if elec_bill else None
            water_total = water_bill.total_amount if water_bill else None

            # Faltante de areas comunes: lo asume el propietario.
            elec_common = money(elec_total - elec_billed) if elec_total is not None else None
            water_common = money(water_total - water_billed) if water_total is not None else None

            elec_kw_common = None
            if elec_bill and elec_bill.total_units is not None:
                elec_kw_common = money(elec_bill.total_units - total_kw)

            return {
                'period': period,
                'units': [c.to_dict() for c in charges],
                'electricity': {
                    'bill_total': float(money(elec_total)) if elec_total is not None else None,
                    'bill_kw': float(elec_bill.total_units) if elec_bill else None,
                    'unit_price': float(elec_bill.unit_price) if elec_bill else None,
                    'billed_to_units': float(money(elec_billed)),
                    'kw_billed_to_units': float(total_kw),
                    'common_area_amount': float(elec_common) if elec_common is not None else None,
                    'common_area_kw': float(elec_kw_common) if elec_kw_common is not None else None,
                },
                'water': {
                    'bill_total': float(money(water_total)) if water_total is not None else None,
                    'bill_people': float(water_bill.total_units) if water_bill else None,
                    'unit_price': float(water_bill.unit_price) if water_bill else None,
                    'billed_to_units': float(money(water_billed)),
                    'prorated_billed': float(water_prorated),
                    'flat_billed': float(money(water_flat)),
                    'common_area_amount': float(water_common) if water_common is not None else None,
                },
                'internet': {
                    'billed_to_units': float(money(internet_billed)),
                },
                'totals': {
                    'billed': float(money(total_billed)),
                    'paid': float(money(total_paid)),
                    'pending': float(money(total_billed - total_paid)),
                    'owner_absorbed': float(money((elec_common or ZERO) + (water_common or ZERO))),
                },
            }
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None

    # ------------------------------------------------------------------
    # Pagos
    # ------------------------------------------------------------------

    @classmethod
    def register_payment(cls, charge_id, amount, payment_date=None, method=None,
                         reference=None, notes=None):
        """Registra un pago y actualiza el estado y el saldo a favor del cargo."""
        try:
            charge = UnitChargeEntity.query.get(charge_id)
            if not charge:
                return None

            payment = PaymentEntity(
                charge_id=charge_id,
                amount=Decimal(str(amount)),
                payment_date=payment_date or date.today(),
                method=method, reference=reference, notes=notes)
            db.session.add(payment)
            db.session.flush()

            cls._recalculate_charge_status(charge)
            db.session.commit()
            return payment.to_dict()
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None

    @classmethod
    def delete_payment(cls, payment_id):
        """Elimina un pago y recalcula el estado del cargo."""
        try:
            payment = PaymentEntity.query.get(payment_id)
            if not payment:
                return False
            charge = payment.charge
            db.session.delete(payment)
            db.session.flush()
            if charge:
                # La coleccion charge.payments puede seguir cacheada con el pago
                # recien borrado, asi que se refresca antes de recalcular.
                db.session.refresh(charge)
                cls._recalculate_charge_status(charge)
            db.session.commit()
            return True
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return False

    @classmethod
    def _recalculate_charge_status(cls, charge):
        """Actualiza paid_amount, credit_balance y status desde los pagos.

        Un pago por encima del total genera saldo a favor, que el periodo
        siguiente arrastra automaticamente via get_previous_credit().
        """
        # Se consultan los pagos contra la base en vez de usar charge.payments,
        # que puede venir cacheado tras un alta o una baja en la misma sesion.
        payments = PaymentEntity.query.filter_by(charge_id=charge.charge_id).all()
        paid = sum((p.amount or ZERO for p in payments), ZERO)
        total = charge.total_amount or ZERO

        charge.paid_amount = money(paid)
        charge.credit_balance = money(paid - total) if paid > total else ZERO

        if paid <= ZERO:
            charge.status = STATUS_PENDING
        elif paid < total:
            charge.status = STATUS_PARTIAL
        else:
            charge.status = STATUS_PAID

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    @classmethod
    def get_charges(cls, period=None, unit_id=None, status=None):
        """Lista de cargos con filtros opcionales."""
        try:
            query = UnitChargeEntity.query.join(UnitEntity)
            if period:
                query = query.filter(UnitChargeEntity.period == period)
            if unit_id:
                query = query.filter(UnitChargeEntity.unit_id == unit_id)
            if status:
                query = query.filter(UnitChargeEntity.status == status)
            charges = query.order_by(UnitChargeEntity.period.desc(), UnitEntity.code).all()
            return [c.to_dict() for c in charges]
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return []

    @classmethod
    def get_charge_detail(cls, charge_id):
        """Detalle de un cargo con sus lecturas y pagos: el recibo del inquilino."""
        try:
            charge = UnitChargeEntity.query.get(charge_id)
            if not charge:
                return None

            readings = (MeterReadingEntity.query
                        .join(MeterEntity)
                        .filter(MeterEntity.unit_id == charge.unit_id,
                                MeterReadingEntity.period == charge.period)
                        .all())

            data = charge.to_dict()
            data['readings'] = [r.to_dict() for r in readings]
            data['payments'] = [p.to_dict() for p in charge.payments]
            return data
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None

    @classmethod
    def get_unit_history(cls, unit_id, limit=12):
        """Historico de consumo de una unidad, para comparar y detectar anomalias."""
        try:
            charges = (UnitChargeEntity.query
                       .filter_by(unit_id=unit_id)
                       .order_by(UnitChargeEntity.period.desc())
                       .limit(limit).all())
            return [c.to_dict() for c in reversed(charges)]
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return []

    @classmethod
    def get_consumption_alerts(cls, period, threshold=Decimal('0.4')):
        """Unidades cuyo consumo se desvia del promedio historico.

        Un salto fuerte suele ser fuga, medidor mal leido o lectura invertida.
        """
        try:
            alerts = []
            charges = UnitChargeEntity.query.filter_by(period=period).all()
            for charge in charges:
                history = (UnitChargeEntity.query
                           .filter(UnitChargeEntity.unit_id == charge.unit_id,
                                   UnitChargeEntity.period < period)
                           .order_by(UnitChargeEntity.period.desc())
                           .limit(6).all())
                values = [c.electricity_consumption for c in history
                          if c.electricity_consumption is not None and c.electricity_consumption > ZERO]
                if len(values) < 2:
                    continue

                average = sum(values, ZERO) / Decimal(len(values))
                current = charge.electricity_consumption or ZERO
                if average == ZERO:
                    continue

                variation = (current - average) / average
                if abs(variation) >= threshold:
                    alerts.append({
                        'unit_id': charge.unit_id,
                        'unit_code': charge.unit.code if charge.unit else None,
                        'period': period,
                        'consumption': float(current),
                        'average': float(money(average)),
                        'variation_pct': float(money(variation * 100)),
                        'direction': 'alza' if variation > 0 else 'baja',
                    })
            return alerts
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return []
