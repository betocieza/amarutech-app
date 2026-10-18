#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida el motor de calculo contra los datos reales del Excel historico.

Levanta una base SQLite temporal, importa el Excel y comprueba que:
  - las tarifas coinciden con las del recibo global
  - el consumo por unidad suma todos sus medidores (caso 303)
  - el arrastre de saldo a favor funciona
  - el faltante de areas comunes cuadra con el Excel
  - los pagos actualizan estado y saldo correctamente

Uso:
    python test_billing.py
"""

import os
import sys
import tempfile
from decimal import Decimal

sys.path.insert(0, '.')

from flask import Flask
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
from src.services.UtilityMasterService import UtilityMasterService
from src.services.UtilityBillingService import (UtilityBillingService, money,
                                                period_bounds, previous_period)

EXCEL = 'src/database/Recibos servicios.xlsx'

results = {'pass': 0, 'fail': 0}


def check(name, condition, detail=''):
    if condition:
        results['pass'] += 1
        print('  OK   %s' % name)
    else:
        results['fail'] += 1
        print('  FALLA %s %s' % (name, detail))


def build_app(db_path):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % db_path
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app


def load_excel(app):
    """Importa el Excel usando las funciones del importador."""
    import importlib.util
    import openpyxl
    spec = importlib.util.spec_from_file_location('imp', 'import_recibos_excel.py')
    imp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(imp)

    stats = dict.fromkeys(
        ['units_created', 'tenants_created', 'meters_created', 'bills_created',
         'bills_updated', 'readings_created', 'readings_updated', 'charges_created',
         'charges_updated', 'blocks_skipped', 'price_mismatch'], 0)
    wb = openpyxl.load_workbook(EXCEL, data_only=True)
    imp.import_utility_bills(wb, stats, False)
    db.session.flush()
    for sheet in imp.UNIT_SHEETS:
        if sheet in wb.sheetnames:
            imp.import_unit_sheet(wb, sheet, stats, False)
    db.session.commit()
    return stats


# ---------------------------------------------------------------------------
# Pruebas
# ---------------------------------------------------------------------------

def test_helpers():
    print('\n== helpers ==')
    check('period_bounds de un mes de 31 dias',
          period_bounds('2026-03') == (__import__('datetime').date(2026, 3, 1),
                                       __import__('datetime').date(2026, 3, 31)))
    check('period_bounds de febrero',
          period_bounds('2026-02')[1].day == 28)
    check('period_bounds de diciembre',
          period_bounds('2025-12')[1].day == 31)
    check('previous_period dentro del anio', previous_period('2026-03') == '2026-02')
    check('previous_period cruzando anio', previous_period('2026-01') == '2025-12')
    check('money redondea a 2 decimales', money(Decimal('22.478532')) == Decimal('22.48'))
    check('money con None devuelve 0', money(None) == Decimal('0'))


def test_prices():
    print('\n== tarifas del recibo global ==')
    # De la hoja RECIBOS: marzo total 150.7 / 151 KW
    price = UtilityBillingService.get_unit_price(SERVICE_ELECTRICITY, '2026-03')
    expected = Decimal('150.7') / Decimal('151')
    check('tarifa de luz de marzo 2026', price is not None and abs(price - expected) < Decimal('0.000001'),
          '(obtenido %s, esperado %s)' % (price, expected))

    # Agua marzo: 116.6 / 10 personas = 11.66
    wprice = UtilityBillingService.get_unit_price(SERVICE_WATER, '2026-03')
    check('tarifa de agua de marzo 2026', wprice is not None and abs(wprice - Decimal('11.66')) < Decimal('0.000001'),
          '(obtenido %s)' % wprice)

    check('periodo sin recibo devuelve None',
          UtilityBillingService.get_unit_price(SERVICE_ELECTRICITY, '2030-01') is None)


def test_multi_meter_consumption():
    print('\n== consumo con varios medidores (caso 303) ==')
    unit = UnitEntity.query.filter_by(code='303').first()
    check('existe la unidad 303', unit is not None)
    if not unit:
        return

    # En 2026-05 el 303 consumio por el medidor 301 (4.7 KW) y el 303 (36 KW)
    consumption = UtilityBillingService.get_unit_consumption(unit.unit_id, '2026-05')
    check('consumo del 303 en 2026-05 suma ambos medidores',
          consumption == Decimal('40.7'), '(obtenido %s, esperado 40.7)' % consumption)

    readings = (MeterReadingEntity.query.join(MeterEntity)
                .filter(MeterEntity.unit_id == unit.unit_id,
                        MeterReadingEntity.period == '2026-05').all())
    check('el periodo tiene 2 lecturas registradas', len(readings) == 2,
          '(obtenido %d)' % len(readings))

    codes = sorted(r.meter.code for r in readings)
    check('las lecturas son de los medidores 301 y 303', codes == ['301', '303'],
          '(obtenido %s)' % codes)


def test_occupancy_filter():
    print('\n== solo unidades ocupadas ==')
    from datetime import date

    # El 301 quedo libre: su inquilino paso al 303 el 04-05-2026
    unit301 = UnitEntity.query.filter_by(code='301').first()
    tenant301 = TenantEntity.query.filter_by(unit_id=unit301.unit_id).first()
    tenant301.end_date = date(2026, 5, 4)
    db.session.commit()

    codes = [u.code for u in UtilityBillingService.get_occupied_units('2026-03')]
    check('en marzo el 301 estaba ocupado', '301' in codes, '(ocupadas %s)' % codes)

    codes = [u.code for u in UtilityBillingService.get_occupied_units('2026-10')]
    check('en octubre el 301 ya no figura', '301' not in codes, '(ocupadas %s)' % codes)
    check('las demas unidades siguen apareciendo', '303' in codes, '(ocupadas %s)' % codes)

    # Generar no debe crear cobro para una unidad vacia
    UtilityBillingService.generate_period('2026-10')
    charge = UnitChargeEntity.query.filter_by(unit_id=unit301.unit_id, period='2026-10').first()
    check('no se genera cobro para la unidad vacia', charge is None)

    # Un cobro viejo de una unidad que quedo vacia se elimina al regenerar
    stale = UnitChargeEntity(unit_id=unit301.unit_id, period='2026-10',
                             total_amount=Decimal('0'), paid_amount=Decimal('0'))
    db.session.add(stale)
    db.session.commit()
    summary = UtilityBillingService.generate_period('2026-10')
    check('el cobro huerfano se elimina', '301' in (summary.get('removed') or []),
          '(eliminados %s)' % summary.get('removed'))
    check('el resumen ya no lista la unidad vacia',
          '301' not in [u['unit_code'] for u in summary['units']],
          '(unidades %s)' % [u['unit_code'] for u in summary['units']])

    # Pero uno con pagos NO se borra: perderia la plata cobrada
    paid = UnitChargeEntity(unit_id=unit301.unit_id, period='2026-10',
                            total_amount=Decimal('50'), paid_amount=Decimal('50'))
    db.session.add(paid)
    db.session.commit()
    summary = UtilityBillingService.generate_period('2026-10')
    survivor = UnitChargeEntity.query.filter_by(unit_id=unit301.unit_id, period='2026-10').first()
    check('un cobro con pagos no se borra', survivor is not None)
    check('el resumen avisa por que se conservo',
          any(x['unit_code'] == '301' for x in (summary.get('skipped') or [])),
          '(omitidos %s)' % summary.get('skipped'))
    if survivor:
        db.session.delete(survivor)
        db.session.commit()

    # La planilla de lecturas tampoco debe pedir lecturas de una unidad vacia
    rows = UtilityMasterService.get_reading_sheet('2026-10')
    check('la planilla omite la unidad vacia',
          '301' not in [r['unit_code'] for r in rows],
          '(deptos %s)' % sorted({r['unit_code'] for r in rows}))

    # Un medidor con vigencia cerrada no debe pedir lectura
    meter = MeterEntity.query.filter_by(code='301').filter(
        MeterEntity.unit_id != unit301.unit_id).first()
    if meter:
        meter.valid_to = date(2026, 5, 7)
        db.session.commit()
        rows = UtilityMasterService.get_reading_sheet('2026-10')
        pairs = [(r['unit_code'], r['meter_code']) for r in rows]
        check('un medidor reemplazado no pide lectura',
              ('303', '301') not in pairs, '(renglones %s)' % pairs)
        rows_may = UtilityMasterService.get_reading_sheet('2026-05')
        pairs_may = [(r['unit_code'], r['meter_code']) for r in rows_may]
        check('pero si aparece en el mes del cambio',
              ('303', '301') in pairs_may, '(renglones %s)' % pairs_may)

    # Restaurar para no afectar las pruebas que siguen
    tenant301.end_date = None
    db.session.commit()


def test_cycle_dates():
    print('\n== ciclo de facturacion por unidad ==')
    from datetime import date
    # El 304 se lee del 20 al 20 desde que ingreso SUSAN SUAREZ el 20-03-2026
    unit = UnitEntity.query.filter_by(code='304').first()
    start, end = UtilityBillingService.get_unit_cycle(unit.unit_id, '2026-03')
    check('el ciclo del 304 arranca el 20', start == date(2026, 3, 20),
          '(obtenido %s)' % start)
    check('el ciclo del 304 cierra el 20', end == date(2026, 4, 20),
          '(obtenido %s)' % end)

    # El 303 tiene dos medidores en 2026-05: el ciclo debe cubrir ambos tramos
    unit303 = UnitEntity.query.filter_by(code='303').first()
    start, end = UtilityBillingService.get_unit_cycle(unit303.unit_id, '2026-05')
    check('con dos medidores toma la fecha mas temprana', start == date(2026, 5, 4),
          '(obtenido %s)' % start)
    check('con dos medidores toma la fecha mas tardia', end == date(2026, 6, 4),
          '(obtenido %s)' % end)

    # Al generar, el cargo debe quedar con el ciclo real y no con el mes calendario
    UtilityBillingService.generate_period('2026-03')
    charge = UnitChargeEntity.query.filter_by(unit_id=unit.unit_id, period='2026-03').first()
    check('generate_period respeta el ciclo del 304',
          charge.period_start == date(2026, 3, 20) and charge.period_end == date(2026, 4, 20),
          '(obtenido %s al %s)' % (charge.period_start, charge.period_end))
    check('el ciclo NO es el mes calendario',
          not (charge.period_start == date(2026, 3, 1)
               and charge.period_end == date(2026, 3, 31)))

    # Sin lecturas fechadas cae al mes calendario, que es el respaldo
    start, end = UtilityBillingService.get_unit_cycle(unit.unit_id, '2030-01')
    check('sin lecturas devuelve None', start is None and end is None)


def test_generate_period():
    print('\n== generacion de cobros ==')
    summary = UtilityBillingService.generate_period('2026-06')
    check('generate_period devuelve resumen', summary is not None)
    if not summary:
        return

    check('el resumen trae las unidades', len(summary['units']) > 0)
    check('el resumen trae el cuadre de luz', summary['electricity']['bill_total'] is not None)

    # La tarifa aplicada debe ser la del recibo global del periodo
    price = UtilityBillingService.get_unit_price(SERVICE_ELECTRICITY, '2026-06')
    for u in summary['units']:
        if u['electricity_consumption'] and u['electricity_consumption'] > 0:
            applied = Decimal(str(u['electricity_price']))
            check('unidad %s usa la tarifa del recibo global' % u['unit_code'],
                  abs(applied - price) < Decimal('0.000001'),
                  '(aplicada %s, global %s)' % (applied, price))
            # El importe debe ser consumo x tarifa
            expected = money(Decimal(str(u['electricity_consumption'])) * price)
            got = Decimal(str(u['electricity_amount']))
            check('unidad %s: importe = consumo x tarifa' % u['unit_code'],
                  got == expected, '(obtenido %s, esperado %s)' % (got, expected))


def test_common_area():
    print('\n== faltante de areas comunes ==')
    summary = UtilityBillingService.generate_period('2026-06')
    if not summary:
        check('resumen disponible', False)
        return

    elec = summary['electricity']
    bill_total = Decimal(str(elec['bill_total']))
    billed = Decimal(str(elec['billed_to_units']))
    common = Decimal(str(elec['common_area_amount']))

    check('faltante = recibo global - repartido',
          common == money(bill_total - billed),
          '(global %s - repartido %s = %s, obtenido %s)' % (bill_total, billed, bill_total - billed, common))

    check('el faltante se reporta, no se reparte',
          billed < bill_total or common <= Decimal('0.01'),
          '(el repartido no deberia exceder el recibo global)')

    # KW de areas comunes
    if elec['common_area_kw'] is not None:
        kw_common = Decimal(str(elec['common_area_kw']))
        expected_kw = money(Decimal(str(elec['bill_kw'])) - Decimal(str(elec['kw_billed_to_units'])))
        check('KW de areas comunes cuadra', kw_common == expected_kw,
              '(obtenido %s, esperado %s)' % (kw_common, expected_kw))

    check('owner_absorbed refleja el faltante',
          summary['totals']['owner_absorbed'] is not None)


def test_payments_and_credit():
    print('\n== pagos, saldo a favor y arrastre ==')
    unit = UnitEntity.query.filter_by(code='301').first()
    # Marzo, no febrero: el saldo a favor es del inquilino, y el inquilino del
    # 301 recien entra en marzo.
    charge = UnitChargeEntity.query.filter_by(unit_id=unit.unit_id, period='2026-03').first()
    check('existe el cargo del 301 en 2026-03', charge is not None)
    if not charge:
        return
    check('el cargo tiene inquilino', charge.tenant_id is not None)

    total = charge.total_amount
    # Pago parcial
    UtilityBillingService.register_payment(charge.charge_id, money(total / 2))
    db.session.refresh(charge)
    check('pago parcial marca estado parcial', charge.status == STATUS_PARTIAL,
          '(estado %s)' % charge.status)
    check('pago parcial no genera saldo a favor', charge.credit_balance == Decimal('0'))

    # Completar el pago con exceso: el Excel tenia 45.31 pagados sobre 37.83
    excess = Decimal('10.00')
    UtilityBillingService.register_payment(charge.charge_id, money(total / 2) + excess)
    db.session.refresh(charge)
    check('pago completo marca estado pagado', charge.status == STATUS_PAID,
          '(estado %s)' % charge.status)
    check('el exceso genera saldo a favor',
          abs(charge.credit_balance - excess) <= Decimal('0.01'),
          '(saldo %s, esperado %s)' % (charge.credit_balance, excess))

    # El saldo a favor debe arrastrarse al periodo siguiente
    credit = UtilityBillingService.get_previous_credit(charge.tenant_id, '2026-04')
    check('el saldo a favor se arrastra al periodo siguiente',
          abs(credit - excess) <= Decimal('0.01'),
          '(arrastrado %s, esperado %s)' % (credit, excess))

    # Y debe aplicarse al regenerar
    UtilityBillingService.generate_period('2026-04')
    next_charge = UtilityBillingService.get_charges(period='2026-04', unit_id=unit.unit_id)
    check('existe el cargo siguiente del 301', bool(next_charge))
    if next_charge:
        applied = Decimal(str(next_charge[0]['previous_credit']))
        check('el cargo siguiente aplica el saldo a favor',
              abs(applied - excess) <= Decimal('0.01'),
              '(aplicado %s)' % applied)
        # total = luz + agua + internet - credito
        c = next_charge[0]
        expected = money(Decimal(str(c['electricity_amount'])) + Decimal(str(c['water_amount']))
                         + Decimal(str(c['internet_amount'])) - applied)
        check('total = luz + agua + internet - saldo a favor',
              Decimal(str(c['total_amount'])) == expected,
              '(obtenido %s, esperado %s)' % (c['total_amount'], expected))

    # El saldo es del inquilino: uno nuevo en el mismo departamento arranca de
    # cero y no hereda lo que pago de mas el anterior.
    check('sin inquilino no hay saldo a favor',
          UtilityBillingService.get_previous_credit(None, '2026-04') == Decimal('0'))
    otro = (TenantEntity.query
            .filter(TenantEntity.tenant_id != charge.tenant_id).first())
    if otro:
        check('otro inquilino no hereda el saldo a favor',
              UtilityBillingService.get_previous_credit(otro.tenant_id, '2026-04')
              == Decimal('0'))


def test_payment_deletion():
    print('\n== eliminacion de pago ==')
    unit = UnitEntity.query.filter_by(code='304').first()
    charge = UnitChargeEntity.query.filter_by(unit_id=unit.unit_id, period='2026-04').first()
    if not charge:
        check('existe cargo del 304', False)
        return

    payment = UtilityBillingService.register_payment(charge.charge_id, charge.total_amount)
    db.session.refresh(charge)
    check('el cargo queda pagado', charge.status == STATUS_PAID)

    UtilityBillingService.delete_payment(payment['payment_id'])
    db.session.refresh(charge)
    check('al borrar el pago vuelve a pendiente', charge.status == STATUS_PENDING,
          '(estado %s)' % charge.status)
    check('al borrar el pago el monto pagado vuelve a 0',
          charge.paid_amount == Decimal('0'), '(pagado %s)' % charge.paid_amount)


def test_paid_charge_not_recalculated():
    print('\n== proteccion de cargos con pagos ==')
    unit = UnitEntity.query.filter_by(code='201').first()
    charge = UnitChargeEntity.query.filter_by(unit_id=unit.unit_id, period='2026-07').first()
    if not charge:
        check('existe cargo del 201 en 2026-07', False)
        return

    UtilityBillingService.register_payment(charge.charge_id, Decimal('10.00'))
    db.session.refresh(charge)
    before = charge.total_amount

    summary = UtilityBillingService.generate_period('2026-07')
    db.session.refresh(charge)
    check('un cargo con pagos no se recalcula', charge.total_amount == before,
          '(antes %s, despues %s)' % (before, charge.total_amount))
    codes = [s['unit_code'] for s in summary['skipped']]
    check('el resumen reporta el cargo omitido', '201' in codes, '(omitidos %s)' % codes)


def test_alerts():
    print('\n== alertas de consumo ==')
    alerts = UtilityBillingService.get_consumption_alerts('2026-08')
    check('get_consumption_alerts devuelve lista', isinstance(alerts, list))
    for a in alerts:
        check('la alerta de %s trae variacion' % a['unit_code'],
              'variation_pct' in a and a['direction'] in ('alza', 'baja'))
    print('     alertas detectadas: %d %s' % (
        len(alerts), [(a['unit_code'], a['variation_pct']) for a in alerts]))


def test_missing_bill():
    print('\n== periodo sin recibo global ==')
    summary = UtilityBillingService.generate_period('2026-11')
    check('genera igual sin recibo cargado', summary is not None)
    if summary:
        check('avisa que falta el recibo de luz',
              any('luz' in w for w in summary['warnings']),
              '(avisos %s)' % summary['warnings'])
        check('avisa que falta el recibo de agua',
              any('agua' in w for w in summary['warnings']))
        check('sin tarifa el importe de luz es 0',
              all(u['electricity_amount'] == 0 for u in summary['units']))


def test_water_flat_fee():
    """Tarifa plana de agua: reemplaza el prorrateo solo para ese inquilino."""
    print('\n== tarifa plana de agua ==')
    period = '2026-06'

    unit = UnitEntity.query.filter_by(code='201').first()
    if not unit:
        check('existe la unidad 201', False)
        return
    tenant = UtilityBillingService.get_active_tenant(unit.unit_id, period)
    if not tenant:
        check('el 201 tiene inquilino vigente', False)
        return

    # Punto de partida: sin tarifa plana, con prorrateo.
    before = UtilityBillingService.generate_period(period)
    otra = next((u for u in before['units'] if u['unit_code'] != '201'
                 and u['water_people']), None)
    agua_otros_antes = Decimal(str(otra['water_amount'])) if otra else None
    tarifa_antes = Decimal(str(otra['water_price'])) if otra else None
    total_201_antes = next(Decimal(str(u['total_amount']))
                           for u in before['units'] if u['unit_code'] == '201')
    agua_201_antes = next(Decimal(str(u['water_amount']))
                          for u in before['units'] if u['unit_code'] == '201')

    # Se pacta S/ 20 planos con el inquilino del 201.
    plana = Decimal('20.00')
    tenant.water_flat_fee = plana
    db.session.commit()

    after = UtilityBillingService.generate_period(period)
    u201 = next(u for u in after['units'] if u['unit_code'] == '201')

    check('el 201 paga la tarifa plana',
          Decimal(str(u201['water_amount'])) == plana,
          '(obtenido %s, esperado %s)' % (u201['water_amount'], plana))
    check('el cargo plano no guarda personas', u201['water_people'] == 0)
    check('el cargo plano no guarda tarifa por persona',
          Decimal(str(u201['water_price'])) == Decimal('0'))

    # El total debe moverse exactamente lo que cambio el agua.
    esperado = money(total_201_antes - agua_201_antes + plana)
    check('el total del 201 refleja la tarifa plana',
          Decimal(str(u201['total_amount'])) == esperado,
          '(obtenido %s, esperado %s)' % (u201['total_amount'], esperado))

    # Opcion B: los demas no se ven afectados.
    if otra is not None:
        otra_despues = next(u for u in after['units']
                            if u['unit_code'] == otra['unit_code'])
        check('la tarifa por persona de los demas no cambia',
              Decimal(str(otra_despues['water_price'])) == tarifa_antes,
              '(antes %s, despues %s)' % (tarifa_antes, otra_despues['water_price']))
        check('el agua de los demas no cambia',
              Decimal(str(otra_despues['water_amount'])) == agua_otros_antes,
              '(antes %s, despues %s)' % (agua_otros_antes, otra_despues['water_amount']))

    # El cuadre separa lo plano de lo prorrateado.
    agua = after['water']
    check('el cuadre reporta lo cobrado como tarifa plana',
          Decimal(str(agua['flat_billed'])) == plana,
          '(obtenido %s)' % agua['flat_billed'])
    check('plano + prorrateado = total cobrado de agua',
          money(Decimal(str(agua['flat_billed'])) + Decimal(str(agua['prorated_billed'])))
          == money(Decimal(str(agua['billed_to_units']))))
    check('el 201 no entra en lo prorrateado',
          Decimal(str(agua['prorated_billed'])) < Decimal(str(agua['billed_to_units'])))

    # Quitarla devuelve al inquilino al prorrateo.
    tenant.water_flat_fee = None
    db.session.commit()
    back = UtilityBillingService.generate_period(period)
    u201 = next(u for u in back['units'] if u['unit_code'] == '201')
    check('sin tarifa plana vuelve al prorrateo',
          Decimal(str(u201['water_amount'])) == agua_201_antes,
          '(obtenido %s, esperado %s)' % (u201['water_amount'], agua_201_antes))
    check('vuelve a registrar las personas', u201['water_people'] > 0)


def main():
    fd, db_path = tempfile.mkstemp(suffix='.db', prefix='test_billing_')
    os.close(fd)
    os.unlink(db_path)

    app = build_app(db_path)
    try:
        with app.app_context():
            db.create_all()
            stats = load_excel(app)
            print('Excel importado: %d unidades, %d medidores, %d lecturas, %d cargos'
                  % (stats['units_created'], stats['meters_created'],
                     stats['readings_created'], stats['charges_created']))

            test_helpers()
            test_prices()
            test_multi_meter_consumption()
            test_cycle_dates()
            test_occupancy_filter()
            test_generate_period()
            test_common_area()
            test_payments_and_credit()
            test_payment_deletion()
            test_paid_charge_not_recalculated()
            test_alerts()
            test_missing_bill()
            test_water_flat_fee()

        print('\n' + '=' * 60)
        print('RESULTADO: %d OK, %d fallas' % (results['pass'], results['fail']))
        print('=' * 60)
        return 1 if results['fail'] else 0
    finally:
        # En Windows SQLite mantiene el archivo tomado hasta que se cierra el
        # engine, asi que se libera antes de borrar.
        try:
            with app.app_context():
                db.engine.dispose()
        except Exception:
            pass
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except OSError:
                pass


if __name__ == '__main__':
    sys.exit(main())
