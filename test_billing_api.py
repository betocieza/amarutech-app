#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida la API REST del modulo de recibos.

Levanta la app Flask sobre una SQLite temporal cargada con el Excel real y
ejercita los endpoints con el test client, incluyendo autenticacion.

Uso:
    python test_billing_api.py
"""

import os
import sys
import tempfile
from decimal import Decimal

sys.path.insert(0, '.')

import jwt
from flask import Flask
from decouple import config as env_config

from src.database import db
from src.models.UnitEntity import UnitEntity
from src.models.TenantEntity import TenantEntity
from src.models.MeterEntity import MeterEntity
from src.models.UtilityBillEntity import UtilityBillEntity
from src.models.MeterReadingEntity import MeterReadingEntity
from src.models.UnitChargeEntity import UnitChargeEntity
from src.models.PaymentEntity import PaymentEntity

from src.controllers import UtilityMasterController, UtilityBillingController

results = {'pass': 0, 'fail': 0}


def check(name, condition, detail=''):
    if condition:
        results['pass'] += 1
        print('  OK   %s' % name)
    else:
        results['fail'] += 1
        print('  FALLA %s %s' % (name, detail))


def make_token():
    """Token de administrador, firmado con la misma clave que usa Security."""
    payload = {'user_id': 1, 'username': 'test', 'first_name': 'Test',
               'roles': ['Administrator']}
    return jwt.encode(payload, env_config('JWT_KEY'), algorithm='HS256')


def build_app(db_path):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % db_path
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True
    db.init_app(app)
    app.register_blueprint(UtilityMasterController.main, url_prefix='/api/utilities')
    app.register_blueprint(UtilityBillingController.main, url_prefix='/api/billing')
    return app


def load_excel():
    import importlib.util
    import openpyxl
    spec = importlib.util.spec_from_file_location('imp', 'import_recibos_excel.py')
    imp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(imp)
    stats = dict.fromkeys(
        ['units_created', 'tenants_created', 'meters_created', 'bills_created',
         'bills_updated', 'readings_created', 'readings_updated', 'charges_created',
         'charges_updated', 'blocks_skipped', 'price_mismatch'], 0)
    wb = openpyxl.load_workbook('src/database/Recibos servicios.xlsx', data_only=True)
    imp.import_utility_bills(wb, stats, False)
    db.session.flush()
    for sheet in imp.UNIT_SHEETS:
        if sheet in wb.sheetnames:
            imp.import_unit_sheet(wb, sheet, stats, False)
    db.session.commit()


class Api():
    """Wrapper del test client que adjunta el token."""

    def __init__(self, client, token):
        self.client = client
        self.headers = {'Authorization': 'Bearer %s' % token}

    def get(self, url, auth=True):
        return self.client.get(url, headers=self.headers if auth else {})

    def post(self, url, payload=None, auth=True):
        return self.client.post(url, json=payload or {},
                                headers=self.headers if auth else {})

    def put(self, url, payload=None, auth=True):
        return self.client.put(url, json=payload or {},
                               headers=self.headers if auth else {})

    def delete(self, url, auth=True):
        return self.client.delete(url, headers=self.headers if auth else {})


# ---------------------------------------------------------------------------
# Pruebas
# ---------------------------------------------------------------------------

def test_auth(api):
    print('\n== autenticacion ==')
    r = api.get('/api/utilities/units', auth=False)
    check('sin token devuelve 401', r.status_code == 401, '(status %d)' % r.status_code)

    r = api.client.get('/api/utilities/units',
                       headers={'Authorization': 'Bearer token-invalido'})
    check('token invalido devuelve 401', r.status_code == 401, '(status %d)' % r.status_code)

    r = api.get('/api/utilities/units')
    check('con token valido devuelve 200', r.status_code == 200, '(status %d)' % r.status_code)


def test_units(api):
    print('\n== unidades ==')
    r = api.get('/api/utilities/units')
    body = r.get_json()
    check('lista unidades', body['success'] and body['count'] == 4,
          '(count %s)' % body.get('count'))

    r = api.post('/api/utilities/units', {'code': '401', 'description': 'Depto 401',
                                          'floor': 4, 'is_occupied': False})
    check('crea unidad nueva', r.status_code == 201, '(status %d)' % r.status_code)
    new_id = r.get_json()['data']['unit_id']

    r = api.post('/api/utilities/units', {'code': '401'})
    check('rechaza codigo duplicado', r.status_code == 400, '(status %d)' % r.status_code)

    r = api.post('/api/utilities/units', {})
    check('rechaza unidad sin codigo', r.status_code == 400, '(status %d)' % r.status_code)

    r = api.put('/api/utilities/units/%d' % new_id, {'description': 'Actualizado'})
    check('actualiza unidad', r.status_code == 200
          and r.get_json()['data']['description'] == 'Actualizado')

    r = api.get('/api/utilities/units/999999')
    check('unidad inexistente devuelve 404', r.status_code == 404)

    r = api.delete('/api/utilities/units/%d' % new_id)
    check('deshabilita unidad', r.status_code == 200)

    r = api.get('/api/utilities/units')
    check('la unidad deshabilitada sale del listado',
          r.get_json()['count'] == 4, '(count %s)' % r.get_json()['count'])


def test_tenants(api):
    print('\n== inquilinos ==')
    r = api.get('/api/utilities/tenants')
    check('lista inquilinos', r.get_json()['count'] == 4,
          '(count %s)' % r.get_json()['count'])

    units = api.get('/api/utilities/units').get_json()['data']
    unit_id = units[0]['unit_id']

    r = api.post('/api/utilities/tenants', {
        'unit_id': unit_id, 'full_name': 'INQUILINO PRUEBA',
        'start_date': '2026-09-01', 'people_count': 3, 'internet_fee': 25})
    check('crea inquilino', r.status_code == 201, '(status %d)' % r.status_code)
    tenant_id = r.get_json()['data']['tenant_id']
    check('guarda personas e internet',
          r.get_json()['data']['people_count'] == 3
          and r.get_json()['data']['internet_fee'] == 25.0)

    r = api.post('/api/utilities/tenants', {'full_name': 'SIN UNIDAD'})
    check('rechaza inquilino sin unidad ni fecha', r.status_code == 400)

    r = api.put('/api/utilities/tenants/%d' % tenant_id, {'end_date': '2026-12-31'})
    check('registra fecha de salida',
          r.get_json()['data']['end_date'] == '2026-12-31')

    r = api.get('/api/utilities/tenants?unit_id=%d' % unit_id)
    check('filtra inquilinos por unidad', r.get_json()['count'] >= 1)

    api.delete('/api/utilities/tenants/%d' % tenant_id)


def test_meters(api):
    print('\n== medidores ==')
    r = api.get('/api/utilities/meters')
    check('lista medidores', r.get_json()['count'] == 6,
          '(count %s)' % r.get_json()['count'])

    units = {u['code']: u['unit_id'] for u in api.get('/api/utilities/units').get_json()['data']}

    r = api.post('/api/utilities/meters', {
        'unit_id': units['201'], 'code': 'M-TEST', 'valid_from': '2026-09-01'})
    check('crea medidor', r.status_code == 201, '(status %d)' % r.status_code)
    meter_id = r.get_json()['data']['meter_id']

    r = api.put('/api/utilities/meters/%d' % meter_id, {'valid_to': '2026-08-01'})
    check('rechaza vigencia que termina antes de empezar', r.status_code == 400,
          '(status %d)' % r.status_code)

    r = api.post('/api/utilities/meters', {'code': 'SIN-UNIDAD'})
    check('rechaza medidor sin unidad ni fecha', r.status_code == 400)

    # Reemplazo de medidor: el caso del 303
    r = api.post('/api/utilities/meters/replace', {
        'unit_id': units['201'], 'old_meter_id': meter_id,
        'new_code': 'M-NUEVO', 'change_date': '2026-09-15'})
    check('reemplaza medidor', r.status_code == 200, '(status %d)' % r.status_code)
    if r.status_code == 200:
        data = r.get_json()['data']
        check('cierra la vigencia del medidor anterior',
              data['previous']['valid_to'] == '2026-09-15')
        check('abre la vigencia del medidor nuevo',
              data['current']['valid_from'] == '2026-09-15'
              and data['current']['valid_to'] is None)
        api.delete('/api/utilities/meters/%d' % data['current']['meter_id'])

    r = api.post('/api/utilities/meters/replace', {'unit_id': units['201']})
    check('rechaza reemplazo incompleto', r.status_code == 400)

    api.delete('/api/utilities/meters/%d' % meter_id)


def test_readings(api):
    print('\n== lecturas ==')
    r = api.get('/api/utilities/readings?period=2026-05')
    check('lista lecturas del periodo', r.get_json()['count'] >= 1)

    r = api.get('/api/utilities/readings/sheet/2026-10')
    sheet = r.get_json()['data']
    check('planilla trae un renglon por medidor vigente', len(sheet) > 0)
    check('la planilla precarga la lectura anterior',
          all('previous_reading' in row for row in sheet))
    check('la planilla marca lo no registrado',
          all(row['registered'] is False for row in sheet))

    row = sheet[0]
    prev = Decimal(str(row['previous_reading']))

    r = api.post('/api/utilities/readings', {
        'meter_id': row['meter_id'], 'period': '2026-10',
        'current_reading': float(prev + Decimal('30')),
        'current_date': '2026-10-31'})
    check('registra lectura', r.status_code == 201, '(status %d)' % r.status_code)
    check('calcula el consumo solo',
          r.get_json()['data']['consumption'] == 30.0,
          '(consumo %s)' % r.get_json()['data']['consumption'])

    # Lectura menor que la anterior: error de digitacion
    r = api.post('/api/utilities/readings', {
        'meter_id': row['meter_id'], 'period': '2026-11',
        'current_reading': float(prev - Decimal('5'))})
    check('rechaza lectura menor que la anterior', r.status_code == 400,
          '(status %d)' % r.status_code)

    # Carga masiva
    rows = api.get('/api/utilities/readings/sheet/2026-11').get_json()['data']
    payload = [{'meter_id': x['meter_id'], 'period': '2026-11',
                'current_reading': float(Decimal(str(x['previous_reading'])) + Decimal('20'))}
               for x in rows]
    r = api.post('/api/utilities/readings/bulk', {'readings': payload})
    check('carga masiva de lecturas', r.status_code == 200
          and r.get_json()['count'] == len(payload),
          '(guardadas %s de %d)' % (r.get_json().get('count'), len(payload)))

    r = api.post('/api/utilities/readings/bulk', {'readings': []})
    check('rechaza carga masiva vacia', r.status_code == 400)

    r = api.get('/api/utilities/readings/sheet/2026-11')
    check('la planilla marca lo ya registrado',
          all(x['registered'] for x in r.get_json()['data']))


def test_bills(api):
    print('\n== recibos globales ==')
    r = api.get('/api/billing/bills')
    check('lista recibos', r.get_json()['count'] == 15,
          '(count %s)' % r.get_json()['count'])

    r = api.post('/api/billing/bills', {
        'service_type': 'luz', 'period': '2026-11',
        'total_amount': 180.5, 'total_units': 180})
    check('registra recibo de luz', r.status_code == 200, '(status %d)' % r.status_code)
    # unit_price se guarda con 8 decimales
    expected = 180.5 / 180
    got = r.get_json()['data']['unit_price']
    check('calcula la tarifa sola', abs(got - expected) < 1e-8,
          '(obtenido %s, esperado %s)' % (got, expected))

    r = api.post('/api/billing/bills', {
        'service_type': 'agua', 'period': '2026-11',
        'total_amount': 120, 'total_units': 10})
    check('registra recibo de agua', r.status_code == 200)
    check('tarifa de agua por persona', r.get_json()['data']['unit_price'] == 12.0)

    r = api.post('/api/billing/bills', {
        'service_type': 'gas', 'period': '2026-11',
        'total_amount': 10, 'total_units': 1})
    check('rechaza tipo de servicio invalido', r.status_code == 400)

    r = api.post('/api/billing/bills', {
        'service_type': 'luz', 'period': 'noviembre',
        'total_amount': 10, 'total_units': 1})
    check('rechaza periodo con formato invalido', r.status_code == 400)

    r = api.post('/api/billing/bills', {
        'service_type': 'luz', 'period': '2026-12', 'total_amount': 10, 'total_units': 0})
    check('rechaza total_units en cero', r.status_code == 400)

    # Reemplazo del mismo periodo
    r = api.post('/api/billing/bills', {
        'service_type': 'luz', 'period': '2026-11',
        'total_amount': 200, 'total_units': 180})
    check('actualiza el recibo del mismo periodo sin duplicar', r.status_code == 200)
    r = api.get('/api/billing/bills?period=2026-11&service_type=luz')
    check('sigue habiendo un solo recibo de luz del periodo',
          r.get_json()['count'] == 1, '(count %s)' % r.get_json()['count'])


def test_generate_and_summary(api):
    print('\n== generacion y resumen ==')
    r = api.post('/api/billing/generate/2026-11')
    check('genera el periodo', r.status_code == 200, '(status %d)' % r.status_code)
    summary = r.get_json()['data']
    check('el resumen trae unidades', len(summary['units']) > 0)
    check('el resumen no trae avisos con ambos recibos cargados',
          summary['warnings'] == [], '(avisos %s)' % summary['warnings'])

    r = api.post('/api/billing/generate/2026-13')
    check('rechaza mes invalido', r.status_code == 400, '(status %d)' % r.status_code)

    r = api.get('/api/billing/summary/2026-11')
    check('obtiene el resumen', r.status_code == 200)
    s = r.get_json()['data']

    elec = s['electricity']
    check('el resumen cuadra el faltante de areas comunes',
          abs(round(elec['bill_total'] - elec['billed_to_units'], 2)
              - elec['common_area_amount']) < 0.01,
          '(global %s - repartido %s vs %s)' % (
              elec['bill_total'], elec['billed_to_units'], elec['common_area_amount']))
    check('el resumen reporta lo que absorbe el propietario',
          s['totals']['owner_absorbed'] is not None)

    r = api.get('/api/billing/summary/mal-formato')
    check('rechaza periodo mal formado en el resumen', r.status_code == 400)


def test_charges_and_payments(api):
    print('\n== cobros y pagos ==')
    r = api.get('/api/billing/charges?period=2026-11')
    charges = r.get_json()['data']
    check('lista cobros del periodo', len(charges) > 0)

    charge = next((c for c in charges if c['total_amount'] > 0), charges[0])
    charge_id = charge['charge_id']

    r = api.get('/api/billing/charges/%d' % charge_id)
    detail = r.get_json()['data']
    check('el detalle trae lecturas y pagos',
          'readings' in detail and 'payments' in detail)

    r = api.get('/api/billing/charges/999999')
    check('cobro inexistente devuelve 404', r.status_code == 404)

    # Pago parcial
    half = round(charge['total_amount'] / 2, 2)
    r = api.post('/api/billing/payments', {
        'charge_id': charge_id, 'amount': half, 'method': 'yape'})
    check('registra pago', r.status_code == 201, '(status %d)' % r.status_code)
    payment_id = r.get_json()['data']['payment_id']

    r = api.get('/api/billing/charges/%d' % charge_id)
    check('el pago parcial deja el cobro en parcial',
          r.get_json()['data']['status'] == 'parcial',
          '(estado %s)' % r.get_json()['data']['status'])

    r = api.post('/api/billing/payments', {'charge_id': charge_id, 'amount': -5})
    check('rechaza monto negativo', r.status_code == 400)

    r = api.post('/api/billing/payments', {'charge_id': charge_id, 'amount': 'mucho'})
    check('rechaza monto no numerico', r.status_code == 400)

    r = api.post('/api/billing/payments', {'amount': 10})
    check('rechaza pago sin charge_id', r.status_code == 400)

    r = api.post('/api/billing/payments', {'charge_id': 999999, 'amount': 10})
    check('rechaza pago de cobro inexistente', r.status_code == 404)

    # El cobro con pagos no se recalcula
    before = api.get('/api/billing/charges/%d' % charge_id).get_json()['data']['total_amount']
    r = api.post('/api/billing/generate/2026-11')
    after = api.get('/api/billing/charges/%d' % charge_id).get_json()['data']['total_amount']
    check('un cobro con pagos no se recalcula al regenerar', before == after,
          '(antes %s, despues %s)' % (before, after))
    codes = [s['unit_code'] for s in r.get_json()['data']['skipped']]
    check('el resumen reporta el cobro omitido', charge['unit_code'] in codes,
          '(omitidos %s)' % codes)

    # Borrar el pago
    r = api.delete('/api/billing/payments/%d' % payment_id)
    check('elimina el pago', r.status_code == 200)
    r = api.get('/api/billing/charges/%d' % charge_id)
    check('al borrar el pago vuelve a pendiente',
          r.get_json()['data']['status'] == 'pendiente',
          '(estado %s)' % r.get_json()['data']['status'])

    r = api.delete('/api/billing/payments/999999')
    check('pago inexistente devuelve 404', r.status_code == 404)


def test_history_and_alerts(api):
    print('\n== historico y alertas ==')
    units = {u['code']: u['unit_id'] for u in api.get('/api/utilities/units').get_json()['data']}

    r = api.get('/api/billing/units/%d/history' % units['201'])
    check('obtiene el historico del 201', r.status_code == 200 and r.get_json()['count'] > 0)

    r = api.get('/api/billing/units/%d/history?limit=3' % units['201'])
    check('respeta el limite del historico', r.get_json()['count'] <= 3)

    r = api.get('/api/billing/alerts/2026-08')
    check('obtiene alertas', r.status_code == 200)
    alerts = r.get_json()['data']
    check('detecta el salto de consumo del 201 en 2026-08',
          any(a['unit_code'] == '201' for a in alerts),
          '(alertas %s)' % [(a['unit_code'], a['variation_pct']) for a in alerts])

    r = api.get('/api/billing/alerts/formato-malo')
    check('rechaza periodo invalido en alertas', r.status_code == 400)


def main():
    fd, db_path = tempfile.mkstemp(suffix='.db', prefix='test_api_')
    os.close(fd)
    os.unlink(db_path)

    app = build_app(db_path)
    try:
        with app.app_context():
            db.create_all()
            load_excel()

        api = Api(app.test_client(), make_token())
        with app.app_context():
            test_auth(api)
            test_units(api)
            test_tenants(api)
            test_meters(api)
            test_readings(api)
            test_bills(api)
            test_generate_and_summary(api)
            test_charges_and_payments(api)
            test_history_and_alerts(api)

        print('\n' + '=' * 60)
        print('RESULTADO: %d OK, %d fallas' % (results['pass'], results['fail']))
        print('=' * 60)
        return 1 if results['fail'] else 0
    finally:
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
