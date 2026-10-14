from flask import Blueprint, request, jsonify, send_file
import io
import re
import traceback

# Logger
from src.utils.Logger import Logger
# Security
from src.utils.Security import Security
# Models
from src.models.UtilityBillEntity import SERVICE_TYPES
# Services
from src.services.UtilityBillingService import UtilityBillingService
from src.services.UtilityMasterService import UtilityMasterService, parse_date
from src.services.ReceiptPdfService import ReceiptPdfService
# Mailer
from src.utils.Mailer import Mailer

main = Blueprint('utility_billing_blueprint', __name__)

PERIOD_RE = re.compile(r'^\d{4}-(0[1-9]|1[0-2])$')


def unauthorized():
    return jsonify({'message': 'No autorizado', 'success': False}), 401


def invalid_period():
    return jsonify({'message': 'Periodo inválido. Use el formato YYYY-MM',
                    'success': False}), 400


def server_error(context, ex):
    Logger.add_to_log("error", f"Error en {context}: {str(ex)}")
    Logger.add_to_log("error", traceback.format_exc())
    return jsonify({'message': 'Error interno del servidor', 'success': False}), 500


def ok(data, message, count=False):
    body = {'message': message, 'success': True, 'data': data}
    if count:
        body['count'] = len(data)
    return jsonify(body), 200


# ---------------------------------------------------------------------------
# Recibos globales del edificio
# ---------------------------------------------------------------------------

@main.route('/bills', methods=['GET'])
def get_bills():
    """Listar recibos globales"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        bills = UtilityMasterService.get_bills(
            period=request.args.get('period'),
            service_type=request.args.get('service_type'))
        return ok(bills, 'Recibos obtenidos exitosamente', count=True)
    except Exception as ex:
        return server_error('get_bills', ex)


@main.route('/bills', methods=['POST'])
def save_bill():
    """Registrar el recibo global del mes.

    La tarifa se calcula sola: total_amount / total_units. Para luz total_units
    son los KW del edificio; para agua, el total de personas.
    """
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        data = request.get_json() or {}

        service_type = data.get('service_type')
        period = data.get('period')
        total_amount = data.get('total_amount')
        total_units = data.get('total_units')

        if service_type not in SERVICE_TYPES:
            return jsonify({
                'message': 'service_type debe ser uno de: %s' % ', '.join(SERVICE_TYPES),
                'success': False}), 400
        if not period or not PERIOD_RE.match(str(period)):
            return invalid_period()
        if total_amount is None or total_units in (None, 0, '0'):
            return jsonify({
                'message': 'Se requiere total_amount y total_units mayor que cero',
                'success': False}), 400

        bill = UtilityBillingService.save_bill(
            service_type=service_type, period=period,
            total_amount=total_amount, total_units=total_units,
            period_start=parse_date(data.get('period_start')),
            period_end=parse_date(data.get('period_end')),
            due_date=parse_date(data.get('due_date')),
            notes=data.get('notes'))

        if not bill:
            return jsonify({'message': 'No se pudo guardar el recibo',
                            'success': False}), 400
        return ok(bill, 'Recibo guardado exitosamente')
    except Exception as ex:
        return server_error('save_bill', ex)


@main.route('/bills/<int:bill_id>', methods=['DELETE'])
def delete_bill(bill_id):
    """Eliminar recibo global"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        if not UtilityMasterService.delete_bill(bill_id):
            return jsonify({'message': 'Recibo no encontrado', 'success': False}), 404
        return jsonify({'message': 'Recibo eliminado exitosamente', 'success': True}), 200
    except Exception as ex:
        return server_error('delete_bill', ex)


# ---------------------------------------------------------------------------
# Generación y resumen
# ---------------------------------------------------------------------------

@main.route('/generate/<period>', methods=['POST'])
def generate_period(period):
    """Generar los cobros de todas las unidades del periodo.

    Los cargos que ya tienen pagos registrados no se recalculan y se informan
    en 'skipped'.
    """
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        if not PERIOD_RE.match(str(period)):
            return invalid_period()

        summary = UtilityBillingService.generate_period(period)
        if summary is None:
            return jsonify({'message': 'No se pudo generar el periodo',
                            'success': False}), 500
        return ok(summary, 'Periodo %s generado exitosamente' % period)
    except Exception as ex:
        return server_error('generate_period', ex)


@main.route('/summary/<period>', methods=['GET'])
def get_summary(period):
    """Consolidado del periodo, con el faltante de áreas comunes"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        if not PERIOD_RE.match(str(period)):
            return invalid_period()

        summary = UtilityBillingService.get_period_summary(period)
        if summary is None:
            return jsonify({'message': 'No se pudo obtener el resumen',
                            'success': False}), 500
        return ok(summary, 'Resumen obtenido exitosamente')
    except Exception as ex:
        return server_error('get_summary', ex)


# ---------------------------------------------------------------------------
# Cargos
# ---------------------------------------------------------------------------

@main.route('/charges', methods=['GET'])
def get_charges():
    """Listar cobros por unidad"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        charges = UtilityBillingService.get_charges(
            period=request.args.get('period'),
            unit_id=request.args.get('unit_id', type=int),
            status=request.args.get('status'))
        return ok(charges, 'Cobros obtenidos exitosamente', count=True)
    except Exception as ex:
        return server_error('get_charges', ex)


@main.route('/charges/<int:charge_id>', methods=['GET'])
def get_charge_detail(charge_id):
    """Detalle del cobro: el recibo del inquilino, con lecturas y pagos"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        charge = UtilityBillingService.get_charge_detail(charge_id)
        if not charge:
            return jsonify({'message': 'Cobro no encontrado', 'success': False}), 404
        return ok(charge, 'Cobro obtenido exitosamente')
    except Exception as ex:
        return server_error('get_charge_detail', ex)


@main.route('/units/<int:unit_id>/history', methods=['GET'])
def get_unit_history(unit_id):
    """Histórico de consumo de un departamento"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        limit = request.args.get('limit', 12, type=int)
        limit = min(max(limit, 1), 60)
        history = UtilityBillingService.get_unit_history(unit_id, limit=limit)
        return ok(history, 'Histórico obtenido exitosamente', count=True)
    except Exception as ex:
        return server_error('get_unit_history', ex)


@main.route('/alerts/<period>', methods=['GET'])
def get_alerts(period):
    """Departamentos con consumo fuera de su promedio histórico"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        if not PERIOD_RE.match(str(period)):
            return invalid_period()

        alerts = UtilityBillingService.get_consumption_alerts(period)
        return ok(alerts, 'Alertas obtenidas exitosamente', count=True)
    except Exception as ex:
        return server_error('get_alerts', ex)


# ---------------------------------------------------------------------------
# PDF y envío
# ---------------------------------------------------------------------------

@main.route('/charges/<int:charge_id>/pdf', methods=['GET'])
def get_charge_pdf(charge_id):
    """Descargar el recibo del inquilino en PDF"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()

        pdf, filename = ReceiptPdfService.build_receipt(charge_id)
        if not pdf:
            return jsonify({'message': 'No se pudo generar el recibo', 'success': False}), 404

        return send_file(io.BytesIO(pdf), mimetype='application/pdf',
                         as_attachment=True, download_name=filename)
    except Exception as ex:
        return server_error('get_charge_pdf', ex)


@main.route('/charges/<int:charge_id>/send', methods=['POST'])
def send_charge_email(charge_id):
    """Enviar el recibo por correo al inquilino, con el PDF adjunto.

    Si el inquilino no tiene correo registrado se puede indicar uno en el body.
    """
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()

        charge = UtilityBillingService.get_charge_detail(charge_id)
        if not charge:
            return jsonify({'message': 'Cobro no encontrado', 'success': False}), 404

        data = request.get_json(silent=True) or {}
        to_email = data.get('email')
        if not to_email and charge.get('tenant_id'):
            tenant = UtilityMasterService.get_tenant(charge['tenant_id'])
            to_email = (tenant or {}).get('email')

        if not to_email:
            return jsonify({
                'message': 'El inquilino no tiene correo registrado. Indique uno para enviar.',
                'success': False}), 400

        pdf, filename = ReceiptPdfService.build_receipt(charge_id)
        sent = Mailer.send_receipt_email(to_email, charge, pdf_bytes=pdf, pdf_name=filename)

        if not sent:
            return jsonify({
                'message': 'No se pudo enviar el correo. Revise la configuración SMTP.',
                'success': False}), 502

        return ok({'email': to_email}, 'Recibo enviado a %s' % to_email)
    except Exception as ex:
        return server_error('send_charge_email', ex)


@main.route('/send/<period>', methods=['POST'])
def send_period_emails(period):
    """Enviar los recibos del periodo a todos los inquilinos con correo."""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        if not PERIOD_RE.match(str(period)):
            return invalid_period()

        charges = UtilityBillingService.get_charges(period=period)
        sent, skipped, failed = [], [], []

        for item in charges:
            charge = UtilityBillingService.get_charge_detail(item['charge_id'])
            if not charge:
                continue

            to_email = None
            if charge.get('tenant_id'):
                tenant = UtilityMasterService.get_tenant(charge['tenant_id'])
                to_email = (tenant or {}).get('email')

            if not to_email:
                skipped.append({'unit_code': charge.get('unit_code'),
                                'reason': 'sin correo registrado'})
                continue

            pdf, filename = ReceiptPdfService.build_receipt(charge['charge_id'])
            if Mailer.send_receipt_email(to_email, charge, pdf_bytes=pdf, pdf_name=filename):
                sent.append({'unit_code': charge.get('unit_code'), 'email': to_email})
            else:
                failed.append({'unit_code': charge.get('unit_code'), 'email': to_email})

        return ok({'sent': sent, 'skipped': skipped, 'failed': failed},
                  '%d recibo(s) enviado(s), %d omitido(s), %d con error'
                  % (len(sent), len(skipped), len(failed)))
    except Exception as ex:
        return server_error('send_period_emails', ex)


# ---------------------------------------------------------------------------
# Pagos
# ---------------------------------------------------------------------------

@main.route('/payments', methods=['POST'])
def register_payment():
    """Registrar un pago. Si excede el total genera saldo a favor."""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        data = request.get_json() or {}

        charge_id = data.get('charge_id')
        amount = data.get('amount')
        if not charge_id or amount is None:
            return jsonify({'message': 'Se requiere charge_id y amount',
                            'success': False}), 400
        try:
            if float(amount) <= 0:
                return jsonify({'message': 'El monto debe ser mayor que cero',
                                'success': False}), 400
        except (TypeError, ValueError):
            return jsonify({'message': 'El monto no es un número válido',
                            'success': False}), 400

        payment = UtilityBillingService.register_payment(
            charge_id=charge_id, amount=amount,
            payment_date=parse_date(data.get('payment_date')),
            method=data.get('method'), reference=data.get('reference'),
            notes=data.get('notes'))

        if not payment:
            return jsonify({'message': 'Cobro no encontrado', 'success': False}), 404
        return jsonify({'message': 'Pago registrado exitosamente',
                        'success': True, 'data': payment}), 201
    except Exception as ex:
        return server_error('register_payment', ex)


@main.route('/payments/<int:payment_id>', methods=['DELETE'])
def delete_payment(payment_id):
    """Eliminar un pago y recalcular el estado del cobro"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        if not UtilityBillingService.delete_payment(payment_id):
            return jsonify({'message': 'Pago no encontrado', 'success': False}), 404
        return jsonify({'message': 'Pago eliminado exitosamente', 'success': True}), 200
    except Exception as ex:
        return server_error('delete_payment', ex)
