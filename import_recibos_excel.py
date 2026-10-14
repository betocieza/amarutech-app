#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Importador del historico de 'Recibos servicios.xlsx' a las tablas de servicios.

Uso:
    python import_recibos_excel.py --dry-run     # solo muestra lo que haria
    python import_recibos_excel.py               # escribe en la base de datos

Lee el Excel que se venia usando manualmente y carga:
  - units / tenants / meters (con vigencias)
  - utility_bills  (hoja RECIBOS: recibo global de luz y agua por mes)
  - meter_readings (bloques de lectura de cada hoja de departamento)
  - unit_charges   (cobro consolidado por unidad y periodo)

El importador es idempotente: vuelve a ejecutarse sin duplicar filas.
"""

import argparse
import re
import sys
from datetime import date, datetime
from decimal import Decimal

import openpyxl

sys.path.insert(0, '.')

from config import config as app_config
from src import init_app
from src.database import db
from src.models.UnitEntity import UnitEntity
from src.models.TenantEntity import TenantEntity
from src.models.MeterEntity import MeterEntity
from src.models.UtilityBillEntity import (UtilityBillEntity, SERVICE_ELECTRICITY,
                                          SERVICE_WATER)
from src.models.MeterReadingEntity import MeterReadingEntity
from src.models.UnitChargeEntity import UnitChargeEntity, STATUS_PENDING

EXCEL_PATH = 'src/database/Recibos servicios.xlsx'

# Hojas que contienen bloques de recibos por departamento
UNIT_SHEETS = ['201', '301', '303', '304']

MONTHS = {
    'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4, 'MAYO': 5, 'JUNIO': 6,
    'JULIO': 7, 'AGOSTO': 8, 'SETIEMBRE': 9, 'SEPTIEMBRE': 9, 'OCTUBRE': 10,
    'NOVIEMBRE': 11, 'DICIEMBRE': 12,
}

# El Excel arranca en diciembre 2025 y sigue en 2026
YEAR_BY_MONTH = {12: 2025}
DEFAULT_YEAR = 2026

DATE_RE = re.compile(r'(\d{1,2})/(\d{1,2})/(\d{2,4})')


def parse_date(text):
    """Extrae la primera fecha dd/mm/yyyy de un texto."""
    if text is None:
        return None
    if isinstance(text, datetime):
        return text.date()
    if isinstance(text, date):
        return text
    m = DATE_RE.search(str(text))
    if not m:
        return None
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if y < 100:
        y += 2000
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def parse_dates(text):
    """Extrae todas las fechas dd/mm/yyyy de un texto."""
    out = []
    for m in DATE_RE.finditer(str(text or '')):
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        try:
            out.append(date(y, mo, d))
        except ValueError:
            pass
    return out


def to_decimal(value):
    if value is None or value == '':
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def period_of(d):
    """Periodo 'YYYY-MM' al que pertenece una fecha."""
    return '%04d-%02d' % (d.year, d.month) if d else None


def month_to_period(month_name):
    name = str(month_name or '').strip().upper()
    mo = MONTHS.get(name)
    if not mo:
        return None
    year = YEAR_BY_MONTH.get(mo, DEFAULT_YEAR)
    return '%04d-%02d' % (year, mo)


def rows_of(ws):
    """Filas de la hoja como listas, sin la columna A (siempre vacia)."""
    return [list(r) for r in ws.iter_rows(values_only=True)]


def cells(row):
    """Valores no nulos de una fila."""
    return [c for c in row if c is not None and str(c).strip() != '']


# --------------------------------------------------------------------------
# Hoja RECIBOS -> utility_bills
# --------------------------------------------------------------------------

def import_utility_bills(wb, stats, dry_run):
    ws = wb['RECIBOS']
    data = rows_of(ws)

    for row in data:
        vals = [c for c in row]
        # Luz: columnas B..E -> mes, total S/, total KW, precio/kw
        month, total, units = vals[1], vals[2], vals[3]
        if month and month_to_period(month) and total is not None and units:
            _upsert_bill(SERVICE_ELECTRICITY, month_to_period(month),
                         to_decimal(total), to_decimal(units), stats, dry_run)
        # Agua: columnas G..J -> mes, total S/, total personas, precio/persona
        if len(vals) > 8:
            wmonth, wtotal, wunits = vals[6], vals[7], vals[8]
            if wmonth and month_to_period(wmonth) and wtotal is not None and wunits:
                _upsert_bill(SERVICE_WATER, month_to_period(wmonth),
                             to_decimal(wtotal), to_decimal(wunits), stats, dry_run)


def _upsert_bill(service_type, period, total_amount, total_units, stats, dry_run):
    if not period or total_amount is None or not total_units:
        return
    unit_price = total_amount / total_units
    existing = UtilityBillEntity.query.filter_by(
        service_type=service_type, period=period).first()
    if existing:
        existing.total_amount = total_amount
        existing.total_units = total_units
        existing.unit_price = unit_price
        stats['bills_updated'] += 1
    else:
        db.session.add(UtilityBillEntity(
            service_type=service_type, period=period,
            total_amount=total_amount, total_units=total_units,
            unit_price=unit_price))
        stats['bills_created'] += 1
    if dry_run:
        print('  [recibo global] %-4s %s  total=%s  unidades=%s  precio=%.8f'
              % (service_type, period, total_amount, total_units, unit_price))


# --------------------------------------------------------------------------
# Hojas de departamento -> bloques de recibo
# --------------------------------------------------------------------------

def split_blocks(data):
    """Divide la hoja en bloques, cada uno empieza en RECIBO/CONSUMO DE LUZ."""
    starts = []
    for i, row in enumerate(data):
        vals = cells(row)
        if not vals:
            continue
        label = str(vals[0]).upper()
        if label.startswith('RECIBO DE LUZ') or label.startswith('RECIBO  DE LUZ') \
                or label.startswith('CONSUMO DE LUZ'):
            starts.append(i)
    blocks = []
    for n, s in enumerate(starts):
        e = starts[n + 1] if n + 1 < len(starts) else len(data)
        blocks.append(data[s:e])
    return blocks


def parse_block(block):
    """Extrae de un bloque los datos de luz, agua e internet.

    Devuelve un dict con: tenant_name, period_start, period_end, meters
    (lista de lecturas por medidor), water_price, water_people, water_amount,
    internet_amount, previous_credit.
    """
    info = {
        'tenant_name': None, 'period_start': None, 'period_end': None,
        'meters': [], 'water_price': None, 'water_people': None,
        'water_amount': None, 'internet_amount': None, 'previous_credit': None,
        'electricity_price': None, 'electricity_amount': None,
    }
    current_meter = None
    section = 'luz'

    header = cells(block[0])
    if header:
        ds = parse_dates(header[0])
        if len(ds) >= 2:
            info['period_start'], info['period_end'] = ds[0], ds[1]

    for row in block:
        vals = cells(row)
        if not vals:
            continue
        label = str(vals[0]).strip()
        upper = label.upper()
        value = vals[1] if len(vals) > 1 else None

        if upper.startswith('RECIBO') and 'AGUA' in upper:
            section = 'agua'
            ds = parse_dates(label)
            if len(ds) >= 2 and not info['period_start']:
                info['period_start'], info['period_end'] = ds[0], ds[1]
            continue
        if upper.startswith('RECIBO') and 'INTERNET' in upper:
            section = 'internet'
            continue

        if upper.startswith('NOMBRE'):
            info['tenant_name'] = str(value).strip() if value else None
        elif upper == 'PERIODO':
            ds = parse_dates(value)
            if len(ds) >= 2:
                info['period_start'], info['period_end'] = ds[0], ds[1]
        elif upper.startswith('MEDIDOR'):
            # Dos formatos en el Excel: fila 'MEDIDOR | 304' y encabezado
            # 'Medidor 304' sin valor en la columna siguiente.
            if value is not None:
                code = str(int(float(value)))
            else:
                m = re.search(r'(\d{3})', label)
                code = m.group(1) if m else None
            current_meter = {'code': code, 'previous_reading': None,
                             'current_reading': None, 'consumption': None,
                             'previous_date': None, 'current_date': None}
            info['meters'].append(current_meter)
        elif upper.startswith('LECTURA ANTERIOR'):
            if current_meter is None:
                current_meter = {'code': None, 'previous_reading': None,
                                 'current_reading': None, 'consumption': None,
                                 'previous_date': None, 'current_date': None}
                info['meters'].append(current_meter)
            current_meter['previous_reading'] = to_decimal(value)
            current_meter['previous_date'] = parse_date(label)
            # Columnas extra del Excel: pagado / saldo a favor
            if len(vals) >= 5:
                info['previous_credit'] = to_decimal(vals[-1])
        elif upper.startswith('LECTURA ACTUAL'):
            if current_meter is not None:
                current_meter['current_reading'] = to_decimal(value)
                current_meter['current_date'] = parse_date(label)
        elif upper.startswith('TOTAL CONSUMO (KW)'):
            if current_meter is not None:
                current_meter['consumption'] = to_decimal(value)
        elif upper.startswith('PRECIO / KW'):
            # Tarifa efectivamente aplicada en ese bloque del Excel. No siempre
            # coincide con la del recibo global del mismo periodo (ver README).
            if section == 'luz':
                info['electricity_price'] = to_decimal(value)
        elif upper.startswith(('TOTAL CONSUMO (S/)', 'TOTAL DE CONSUMO')) and section == 'luz':
            amount = to_decimal(value)
            if amount is not None:
                info['electricity_amount'] = (info['electricity_amount'] or Decimal('0')) + amount
        elif upper.startswith('SALDO A FAVOR MES ANTERIOR'):
            info['previous_credit'] = to_decimal(value)
        elif section == 'agua':
            if upper.startswith('PRECIO POR PERSONA'):
                info['water_price'] = to_decimal(value)
            elif 'DE PERSONAS' in upper:
                info['water_people'] = int(float(value)) if value else None
            elif upper.startswith('TOTAL CONSUMO (S/)'):
                info['water_amount'] = to_decimal(value)
        elif section == 'internet':
            if upper.startswith('MONTO FIJO') or upper.startswith('TOTAL CONSUMO (S/)'):
                if info['internet_amount'] is None:
                    info['internet_amount'] = to_decimal(value)

    return info


# --------------------------------------------------------------------------
# Maestros
# --------------------------------------------------------------------------

def get_or_create_unit(code, stats, dry_run):
    unit = UnitEntity.query.filter_by(code=code).first()
    if unit:
        return unit
    unit = UnitEntity(code=code, description='Departamento %s' % code,
                      floor=int(code[0]) if code[:1].isdigit() else None,
                      is_occupied=True, enabled=True)
    db.session.add(unit)
    db.session.flush()
    stats['units_created'] += 1
    if dry_run:
        print('  [unidad] %s' % code)
    return unit


def get_or_create_meter(unit, code, first_date, stats, dry_run):
    meter = MeterEntity.query.filter_by(unit_id=unit.unit_id, code=code).first()
    if meter:
        if first_date and meter.valid_from and first_date < meter.valid_from:
            meter.valid_from = first_date
        return meter
    meter = MeterEntity(unit_id=unit.unit_id, code=code,
                        valid_from=first_date or date(2026, 1, 1), enabled=True)
    db.session.add(meter)
    db.session.flush()
    stats['meters_created'] += 1
    if dry_run:
        print('  [medidor] %s -> unidad %s desde %s' % (code, unit.code, first_date))
    return meter


def get_or_create_tenant(unit, name, start_date, people, internet_fee, stats, dry_run):
    if not name:
        return None
    tenant = TenantEntity.query.filter_by(unit_id=unit.unit_id, full_name=name).first()
    if tenant:
        if people and not tenant.people_count:
            tenant.people_count = people
        if internet_fee and not tenant.internet_fee:
            tenant.internet_fee = internet_fee
        if start_date and tenant.start_date and start_date < tenant.start_date:
            tenant.start_date = start_date
        return tenant
    tenant = TenantEntity(unit_id=unit.unit_id, full_name=name,
                          people_count=people or 1,
                          internet_fee=internet_fee or 0,
                          start_date=start_date or date(2026, 1, 1), enabled=True)
    db.session.add(tenant)
    db.session.flush()
    stats['tenants_created'] += 1
    if dry_run:
        print('  [inquilino] %s (unidad %s)' % (name, unit.code))
    return tenant


# --------------------------------------------------------------------------
# Importacion de bloques
# --------------------------------------------------------------------------

def import_unit_sheet(wb, sheet_name, stats, dry_run):
    ws = wb[sheet_name]
    data = rows_of(ws)
    blocks = split_blocks(data)
    unit = get_or_create_unit(sheet_name, stats, dry_run)

    print('Hoja %s: %d bloques de recibo' % (sheet_name, len(blocks)))

    for block in blocks:
        info = parse_block(block)
        # El periodo se ancla al INICIO del ciclo de facturacion: los ciclos van
        # a mitad de mes (ej. 01/03 - 01/04) y anclarlos al fin haria colisionar
        # dos bloques consecutivos en el mismo periodo.
        period_ref = info['period_start'] or info['period_end']
        if not period_ref:
            stats['blocks_skipped'] += 1
            continue
        period = period_of(period_ref)

        tenant = get_or_create_tenant(
            unit, info['tenant_name'], info['period_start'],
            info['water_people'], info['internet_amount'], stats, dry_run)

        # Lecturas por medidor
        total_kw = Decimal('0')
        for m in info['meters']:
            if m['previous_reading'] is None or m['current_reading'] is None:
                continue
            code = m['code'] or sheet_name
            meter = get_or_create_meter(unit, code, m['previous_date'], stats, dry_run)
            consumption = m['consumption']
            if consumption is None:
                consumption = m['current_reading'] - m['previous_reading']
            total_kw += consumption

            existing = MeterReadingEntity.query.filter_by(
                meter_id=meter.meter_id, period=period).first()
            if existing:
                existing.previous_reading = m['previous_reading']
                existing.current_reading = m['current_reading']
                existing.consumption = consumption
                existing.previous_date = m['previous_date']
                existing.current_date = m['current_date']
                stats['readings_updated'] += 1
            else:
                db.session.add(MeterReadingEntity(
                    meter_id=meter.meter_id, period=period,
                    previous_date=m['previous_date'], current_date=m['current_date'],
                    previous_reading=m['previous_reading'],
                    current_reading=m['current_reading'],
                    consumption=consumption))
                stats['readings_created'] += 1

        # Tarifa e importe de luz.
        #
        # Se prioriza lo que el Excel dejo escrito en el bloque, no la tarifa del
        # recibo global del mismo periodo: en el historico varias hojas apuntan a
        # una fila de RECIBOS que no corresponde al mes facturado (ciclos que van
        # a mitad de mes), y un par de bloques usan una tarifa escrita a mano.
        # Recalcular aqui cambiaria montos ya cobrados, asi que se importa el
        # valor historico tal cual y se deja constancia en 'notes'.
        bill = UtilityBillEntity.query.filter_by(
            service_type=SERVICE_ELECTRICITY, period=period).first()
        global_price = bill.unit_price if bill else None

        elec_price = info['electricity_price'] or global_price or Decimal('0')
        elec_amount = info['electricity_amount']
        if elec_amount is None:
            elec_amount = total_kw * elec_price

        price_note = ''
        if global_price is not None and info['electricity_price'] is not None                 and abs(info['electricity_price'] - global_price) > Decimal('0.00001'):
            price_note = (' | tarifa del Excel %.8f != tarifa del recibo global %.8f'
                          % (info['electricity_price'], global_price))
            stats['price_mismatch'] += 1

        water_amount = info['water_amount'] or Decimal('0')
        internet_amount = info['internet_amount'] or Decimal('0')
        previous_credit = info['previous_credit'] or Decimal('0')
        total = elec_amount + water_amount + internet_amount - previous_credit

        existing = UnitChargeEntity.query.filter_by(
            unit_id=unit.unit_id, period=period).first()
        if existing:
            charge = existing
            stats['charges_updated'] += 1
        else:
            charge = UnitChargeEntity(unit_id=unit.unit_id, period=period)
            db.session.add(charge)
            stats['charges_created'] += 1

        charge.tenant_id = tenant.tenant_id if tenant else None
        charge.period_start = info['period_start']
        charge.period_end = info['period_end']
        charge.electricity_consumption = total_kw
        charge.electricity_price = elec_price
        charge.electricity_amount = elec_amount
        charge.water_people = info['water_people'] or 0
        charge.water_price = info['water_price'] or Decimal('0')
        charge.water_amount = water_amount
        charge.internet_amount = internet_amount
        charge.previous_credit = previous_credit
        charge.total_amount = total
        charge.paid_amount = Decimal('0')
        charge.credit_balance = Decimal('0')
        charge.status = STATUS_PENDING
        charge.notes = 'Importado del Excel historico' + price_note

        if dry_run:
            print('  [cargo] %s %s  luz=%.2f (%.2f KW)  agua=%.2f  internet=%.2f  '
                  'credito=%.2f  TOTAL=%.2f'
                  % (unit.code, period, elec_amount, total_kw, water_amount,
                     internet_amount, previous_credit, total))


def main():
    parser = argparse.ArgumentParser(description='Importa el historico de recibos del Excel')
    parser.add_argument('--dry-run', action='store_true',
                        help='Muestra lo que se importaria sin escribir en la base')
    parser.add_argument('--excel', default=EXCEL_PATH, help='Ruta del archivo Excel')
    args = parser.parse_args()

    app = init_app(app_config['development'])

    stats = {
        'units_created': 0, 'tenants_created': 0, 'meters_created': 0,
        'bills_created': 0, 'bills_updated': 0,
        'readings_created': 0, 'readings_updated': 0,
        'charges_created': 0, 'charges_updated': 0, 'blocks_skipped': 0,
        'price_mismatch': 0,
    }

    with app.app_context():
        wb = openpyxl.load_workbook(args.excel, data_only=True)

        print('== Recibos globales (hoja RECIBOS) ==')
        import_utility_bills(wb, stats, args.dry_run)
        db.session.flush()

        print()
        print('== Recibos por departamento ==')
        for sheet in UNIT_SHEETS:
            if sheet in wb.sheetnames:
                import_unit_sheet(wb, sheet, stats, args.dry_run)

        if args.dry_run:
            db.session.rollback()
            print()
            print('DRY RUN: no se escribio nada en la base de datos.')
        else:
            db.session.commit()
            print()
            print('Importacion confirmada.')

        print()
        print('== Resumen ==')
        for k, v in stats.items():
            print('  %-20s %d' % (k, v))


if __name__ == '__main__':
    main()
