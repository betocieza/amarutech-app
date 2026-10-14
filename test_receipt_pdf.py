#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida la generación del PDF del recibo y el envío por correo.

El SMTP se simula: no se envía ningún correo real, se inspecciona el mensaje
que se habría enviado.

Uso:
    python test_receipt_pdf.py
"""

import os
import sys
import tempfile
from decimal import Decimal
from email import message_from_string

sys.path.insert(0, '.')

import jwt
from flask import Flask
from decouple import config as env_config

from src.database import db
from src.models.UnitEntity import UnitEntity
from src.models.TenantEntity import TenantEntity
from src.models.UnitChargeEntity import UnitChargeEntity
from src.services.ReceiptPdfService import (ReceiptPdfService, period_label,
                                            soles, number)
from src.services.UtilityBillingService import UtilityBillingService
from src.utils import Mailer as MailerModule
from src.utils.Mailer import Mailer
from src.controllers import UtilityMasterController, UtilityBillingController

results = {'pass': 0, 'fail': 0}
sent_messages = []


def check(name, condition, detail=''):
    if condition:
        results['pass'] += 1
        print('  OK   %s' % name)
    else:
        results['fail'] += 1
        print('  FALLA %s %s' % (name, detail))


class FakeSMTP():
    """Reemplaza smtplib.SMTP: captura el mensaje en vez de enviarlo."""

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def starttls(self):
        pass

    def login(self, user, password):
        pass

    def sendmail(self, sender, to, message):
        sent_messages.append({'from': sender, 'to': to, 'raw': message})


def make_token():
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


# ---------------------------------------------------------------------------
# Pruebas
# ---------------------------------------------------------------------------

def test_helpers():
    print('\n== helpers de formato ==')
    check('period_label traduce el mes', period_label('2026-03') == 'Marzo 2026',
          '(obtenido %s)' % period_label('2026-03'))
    check('period_label tolera vacío', period_label('') == '')
    check('period_label tolera basura', period_label('xx') == 'xx')
    check('soles formatea con 2 decimales', soles(Decimal('45.678')) == 'S/ 45.68',
          '(obtenido %s)' % soles(Decimal('45.678')))
    check('soles tolera None', soles(None) == 'S/ 0.00')
    check('number redondea', number(Decimal('40.666')) == '40.67',
          '(obtenido %s)' % number(Decimal('40.666')))


def test_pdf_generation():
    print('\n== generación del PDF ==')
    unit = UnitEntity.query.filter_by(code='301').first()
    charge = UnitChargeEntity.query.filter_by(unit_id=unit.unit_id, period='2026-02').first()
    check('existe el cobro del 301', charge is not None)
    if not charge:
        return None

    pdf, filename = ReceiptPdfService.build_receipt(charge.charge_id)
    check('genera el PDF', pdf is not None and len(pdf) > 1000,
          '(tamaño %s)' % (len(pdf) if pdf else 0))
    check('el PDF tiene cabecera válida', pdf[:5] == b'%PDF-',
          '(cabecera %s)' % pdf[:5])
    check('el nombre trae departamento y periodo',
          filename == 'recibo-301-2026-02.pdf', '(obtenido %s)' % filename)

    # El contenido debe traer los datos del recibo
    text = pdf.decode('latin-1', errors='ignore')
    check('el PDF declara el título del recibo', 'Recibo' in text)

    return charge.charge_id


def test_pdf_multi_meter():
    print('\n== PDF con varios medidores (caso 303) ==')
    unit = UnitEntity.query.filter_by(code='303').first()
    charge = UnitChargeEntity.query.filter_by(unit_id=unit.unit_id, period='2026-05').first()
    if not charge:
        check('existe el cobro del 303 en 2026-05', False)
        return

    detail = UtilityBillingService.get_charge_detail(charge.charge_id)
    check('el cobro tiene 2 lecturas', len(detail['readings']) == 2,
          '(obtenido %d)' % len(detail['readings']))

    pdf, _ = ReceiptPdfService.build_receipt(charge.charge_id)
    check('genera el PDF con dos medidores', pdf is not None and pdf[:5] == b'%PDF-')


def test_pdf_missing_charge():
    print('\n== PDF de un cobro inexistente ==')
    pdf, filename = ReceiptPdfService.build_receipt(999999)
    check('devuelve None sin reventar', pdf is None and filename is None)


def test_mailer_attachment(charge_id):
    print('\n== correo con PDF adjunto ==')
    sent_messages.clear()

    detail = UtilityBillingService.get_charge_detail(charge_id)
    pdf, filename = ReceiptPdfService.build_receipt(charge_id)

    ok = Mailer.send_receipt_email('inquilino@example.com', detail,
                                   pdf_bytes=pdf, pdf_name=filename)
    check('el envío reporta éxito', ok is True)
    check('se capturó un mensaje', len(sent_messages) == 1,
          '(capturados %d)' % len(sent_messages))
    if not sent_messages:
        return

    msg = message_from_string(sent_messages[0]['raw'])
    check('el destinatario es correcto', msg['To'] == 'inquilino@example.com')
    check('el asunto trae periodo y departamento',
          '2026-02' in msg['Subject'] and '301' in msg['Subject'],
          '(asunto %s)' % msg['Subject'])
    check('el mensaje es multipart', msg.is_multipart())

    parts = list(msg.walk())
    html = [p for p in parts if p.get_content_type() == 'text/html']
    attachments = [p for p in parts if p.get_filename()]

    check('incluye el cuerpo HTML', len(html) == 1, '(encontrados %d)' % len(html))
    check('incluye un adjunto', len(attachments) == 1,
          '(encontrados %d)' % len(attachments))
    if attachments:
        check('el adjunto es el PDF del recibo',
              attachments[0].get_filename() == filename,
              '(nombre %s)' % attachments[0].get_filename())
        check('el adjunto tiene el contenido del PDF',
              attachments[0].get_payload(decode=True)[:5] == b'%PDF-')

    if html:
        body = html[0].get_payload(decode=True).decode('utf-8', errors='ignore')
        check('el cuerpo muestra el total',
              ('%.2f' % float(detail['total_amount'])) in body,
              '(total %s)' % detail['total_amount'])
        check('el cuerpo menciona el departamento', '301' in body)


def test_mailer_without_attachment():
    print('\n== correo sin adjunto ==')
    sent_messages.clear()
    charge = UnitChargeEntity.query.first()
    detail = UtilityBillingService.get_charge_detail(charge.charge_id)

    Mailer.send_receipt_email('otro@example.com', detail)
    check('se capturó el mensaje', len(sent_messages) == 1)
    if sent_messages:
        msg = message_from_string(sent_messages[0]['raw'])
        attachments = [p for p in msg.walk() if p.get_filename()]
        check('no lleva adjuntos', len(attachments) == 0,
              '(encontrados %d)' % len(attachments))
        html = [p for p in msg.walk() if p.get_content_type() == 'text/html']
        check('conserva el cuerpo HTML', len(html) == 1)


def test_endpoints(app, token):
    print('\n== endpoints de PDF y envío ==')
    client = app.test_client()
    headers = {'Authorization': 'Bearer %s' % token}

    unit = UnitEntity.query.filter_by(code='301').first()
    charge = UnitChargeEntity.query.filter_by(unit_id=unit.unit_id, period='2026-02').first()

    r = client.get('/api/billing/charges/%d/pdf' % charge.charge_id)
    check('el PDF sin token devuelve 401', r.status_code == 401,
          '(status %d)' % r.status_code)

    r = client.get('/api/billing/charges/%d/pdf' % charge.charge_id, headers=headers)
    check('descarga el PDF', r.status_code == 200, '(status %d)' % r.status_code)
    check('el tipo de contenido es PDF', r.mimetype == 'application/pdf',
          '(mimetype %s)' % r.mimetype)
    check('el cuerpo es un PDF', r.data[:5] == b'%PDF-')
    check('se descarga como adjunto',
          'attachment' in (r.headers.get('Content-Disposition') or ''),
          '(header %s)' % r.headers.get('Content-Disposition'))

    r = client.get('/api/billing/charges/999999/pdf', headers=headers)
    check('PDF de cobro inexistente devuelve 404', r.status_code == 404,
          '(status %d)' % r.status_code)

    # Envío: el inquilino del 301 no tiene correo cargado
    sent_messages.clear()
    r = client.post('/api/billing/charges/%d/send' % charge.charge_id,
                    json={}, headers=headers)
    check('sin correo registrado devuelve 400', r.status_code == 400,
          '(status %d)' % r.status_code)
    check('el mensaje explica que falta el correo',
          'correo' in r.get_json()['message'].lower())

    # Con correo explícito en el body
    r = client.post('/api/billing/charges/%d/send' % charge.charge_id,
                    json={'email': 'directo@example.com'}, headers=headers)
    check('envía con el correo indicado en el body', r.status_code == 200,
          '(status %d, %s)' % (r.status_code, r.get_json()))
    check('se envió un mensaje', len(sent_messages) == 1)

    # Con el correo del inquilino cargado en su ficha. Se usa un cobro que
    # tenga inquilino vinculado: los primeros bloques del Excel no traen nombre,
    # asi que su charge queda con tenant_id nulo.
    linked = (UnitChargeEntity.query
              .filter(UnitChargeEntity.tenant_id.isnot(None))
              .first())
    check('hay cobros con inquilino vinculado', linked is not None)
    if not linked:
        return

    tenant = TenantEntity.query.get(linked.tenant_id)
    tenant.email = 'ficha@example.com'
    db.session.commit()

    sent_messages.clear()
    r = client.post('/api/billing/charges/%d/send' % linked.charge_id,
                    json={}, headers=headers)
    check('usa el correo de la ficha del inquilino', r.status_code == 200,
          '(status %d, %s)' % (r.status_code, r.get_json()))
    if sent_messages:
        msg = message_from_string(sent_messages[0]['raw'])
        check('el destinatario sale de la ficha', msg['To'] == 'ficha@example.com',
              '(destinatario %s)' % msg['To'])

    r = client.post('/api/billing/charges/999999/send', json={}, headers=headers)
    check('envío de cobro inexistente devuelve 404', r.status_code == 404)


def test_bulk_send(app, token):
    print('\n== envío masivo del periodo ==')
    client = app.test_client()
    headers = {'Authorization': 'Bearer %s' % token}

    # Se usa el periodo de un cobro que tenga inquilino con correo cargado
    linked = (UnitChargeEntity.query
              .filter(UnitChargeEntity.tenant_id.isnot(None))
              .first())
    period = linked.period if linked else '2026-02'

    sent_messages.clear()
    r = client.post('/api/billing/send/%s' % period, headers=headers)
    check('el envío masivo responde 200', r.status_code == 200,
          '(status %d)' % r.status_code)

    data = r.get_json()['data']
    check('reporta enviados, omitidos y con error',
          'sent' in data and 'skipped' in data and 'failed' in data)
    check('envió al inquilino con correo', len(data['sent']) >= 1,
          '(enviados %s)' % data['sent'])
    check('omitió a los que no tienen correo', len(data['skipped']) >= 1,
          '(omitidos %s)' % data['skipped'])
    check('los omitidos explican el motivo',
          all('correo' in s['reason'] for s in data['skipped']))
    check('la cantidad de correos coincide con los enviados',
          len(sent_messages) == len(data['sent']),
          '(capturados %d vs reportados %d)' % (len(sent_messages), len(data['sent'])))

    r = client.post('/api/billing/send/formato-malo', headers=headers)
    check('rechaza periodo inválido', r.status_code == 400)


def test_smtp_failure(app, token):
    print('\n== fallo de SMTP ==')

    def broken_smtp(host, port):
        raise OSError('conexión rechazada')

    original = MailerModule.smtplib.SMTP
    MailerModule.smtplib.SMTP = broken_smtp
    try:
        client = app.test_client()
        headers = {'Authorization': 'Bearer %s' % token}
        charge = UnitChargeEntity.query.first()
        r = client.post('/api/billing/charges/%d/send' % charge.charge_id,
                        json={'email': 'test@example.com'}, headers=headers)
        check('un SMTP caído devuelve 502', r.status_code == 502,
              '(status %d)' % r.status_code)
        check('el mensaje menciona la configuración SMTP',
              'SMTP' in r.get_json()['message'])
    finally:
        MailerModule.smtplib.SMTP = original


def main():
    fd, db_path = tempfile.mkstemp(suffix='.db', prefix='test_pdf_')
    os.close(fd)
    os.unlink(db_path)

    # SMTP simulado: nada sale a la red
    original_smtp = MailerModule.smtplib.SMTP
    MailerModule.smtplib.SMTP = FakeSMTP

    app = build_app(db_path)
    try:
        with app.app_context():
            db.create_all()
            load_excel()

            token = make_token()
            test_helpers()
            charge_id = test_pdf_generation()
            test_pdf_multi_meter()
            test_pdf_missing_charge()
            if charge_id:
                test_mailer_attachment(charge_id)
            test_mailer_without_attachment()
            test_endpoints(app, token)
            test_bulk_send(app, token)
            test_smtp_failure(app, token)

        print('\n' + '=' * 60)
        print('RESULTADO: %d OK, %d fallas' % (results['pass'], results['fail']))
        print('=' * 60)
        return 1 if results['fail'] else 0
    finally:
        MailerModule.smtplib.SMTP = original_smtp
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
