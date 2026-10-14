from flask import Blueprint, request, jsonify
import traceback

# Logger
from src.utils.Logger import Logger
# Security
from src.utils.Security import Security
# Services
from src.services.UtilityMasterService import UtilityMasterService

main = Blueprint('utility_master_blueprint', __name__)


def unauthorized():
    return jsonify({'message': 'No autorizado', 'success': False}), 401


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
# Unidades
# ---------------------------------------------------------------------------

@main.route('/units', methods=['GET'])
def get_units():
    """Listar departamentos"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        enabled_only = request.args.get('enabled_only', 'true').lower() != 'false'
        units = UtilityMasterService.get_units(enabled_only=enabled_only)
        return ok(units, 'Departamentos obtenidos exitosamente', count=True)
    except Exception as ex:
        return server_error('get_units', ex)


@main.route('/units/<int:unit_id>', methods=['GET'])
def get_unit(unit_id):
    """Obtener un departamento"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        unit = UtilityMasterService.get_unit(unit_id)
        if not unit:
            return jsonify({'message': 'Departamento no encontrado', 'success': False}), 404
        return ok(unit, 'Departamento obtenido exitosamente')
    except Exception as ex:
        return server_error('get_unit', ex)


@main.route('/units', methods=['POST'])
def create_unit():
    """Crear departamento"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        data = request.get_json() or {}
        unit = UtilityMasterService.save_unit(data)
        if not unit:
            return jsonify({
                'message': 'No se pudo crear. Revise que el código sea válido y no esté repetido',
                'success': False}), 400
        return jsonify({'message': 'Departamento creado exitosamente',
                        'success': True, 'data': unit}), 201
    except Exception as ex:
        return server_error('create_unit', ex)


@main.route('/units/<int:unit_id>', methods=['PUT'])
def update_unit(unit_id):
    """Actualizar departamento"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        data = request.get_json() or {}
        unit = UtilityMasterService.save_unit(data, unit_id=unit_id)
        if not unit:
            return jsonify({'message': 'Departamento no encontrado', 'success': False}), 404
        return ok(unit, 'Departamento actualizado exitosamente')
    except Exception as ex:
        return server_error('update_unit', ex)


@main.route('/units/<int:unit_id>', methods=['DELETE'])
def delete_unit(unit_id):
    """Deshabilitar departamento (no se borra para conservar el histórico)"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        if not UtilityMasterService.delete_unit(unit_id):
            return jsonify({'message': 'Departamento no encontrado', 'success': False}), 404
        return jsonify({'message': 'Departamento deshabilitado exitosamente',
                        'success': True}), 200
    except Exception as ex:
        return server_error('delete_unit', ex)


# ---------------------------------------------------------------------------
# Inquilinos
# ---------------------------------------------------------------------------

@main.route('/tenants', methods=['GET'])
def get_tenants():
    """Listar inquilinos"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        unit_id = request.args.get('unit_id', type=int)
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        tenants = UtilityMasterService.get_tenants(unit_id=unit_id, active_only=active_only)
        return ok(tenants, 'Inquilinos obtenidos exitosamente', count=True)
    except Exception as ex:
        return server_error('get_tenants', ex)


@main.route('/tenants/<int:tenant_id>', methods=['GET'])
def get_tenant(tenant_id):
    """Obtener un inquilino"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        tenant = UtilityMasterService.get_tenant(tenant_id)
        if not tenant:
            return jsonify({'message': 'Inquilino no encontrado', 'success': False}), 404
        return ok(tenant, 'Inquilino obtenido exitosamente')
    except Exception as ex:
        return server_error('get_tenant', ex)


@main.route('/tenants', methods=['POST'])
def create_tenant():
    """Crear inquilino"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        data = request.get_json() or {}
        tenant = UtilityMasterService.save_tenant(data)
        if not tenant:
            return jsonify({
                'message': 'No se pudo crear. Se requiere unit_id, full_name y start_date',
                'success': False}), 400
        return jsonify({'message': 'Inquilino creado exitosamente',
                        'success': True, 'data': tenant}), 201
    except Exception as ex:
        return server_error('create_tenant', ex)


@main.route('/tenants/<int:tenant_id>', methods=['PUT'])
def update_tenant(tenant_id):
    """Actualizar inquilino"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        data = request.get_json() or {}
        tenant = UtilityMasterService.save_tenant(data, tenant_id=tenant_id)
        if not tenant:
            return jsonify({'message': 'Inquilino no encontrado', 'success': False}), 404
        return ok(tenant, 'Inquilino actualizado exitosamente')
    except Exception as ex:
        return server_error('update_tenant', ex)


@main.route('/tenants/<int:tenant_id>', methods=['DELETE'])
def delete_tenant(tenant_id):
    """Deshabilitar inquilino"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        if not UtilityMasterService.delete_tenant(tenant_id):
            return jsonify({'message': 'Inquilino no encontrado', 'success': False}), 404
        return jsonify({'message': 'Inquilino deshabilitado exitosamente',
                        'success': True}), 200
    except Exception as ex:
        return server_error('delete_tenant', ex)


# ---------------------------------------------------------------------------
# Medidores
# ---------------------------------------------------------------------------

@main.route('/meters', methods=['GET'])
def get_meters():
    """Listar medidores"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        unit_id = request.args.get('unit_id', type=int)
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        meters = UtilityMasterService.get_meters(unit_id=unit_id, active_only=active_only)
        return ok(meters, 'Medidores obtenidos exitosamente', count=True)
    except Exception as ex:
        return server_error('get_meters', ex)


@main.route('/meters/<int:meter_id>', methods=['GET'])
def get_meter(meter_id):
    """Obtener un medidor"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        meter = UtilityMasterService.get_meter(meter_id)
        if not meter:
            return jsonify({'message': 'Medidor no encontrado', 'success': False}), 404
        return ok(meter, 'Medidor obtenido exitosamente')
    except Exception as ex:
        return server_error('get_meter', ex)


@main.route('/meters', methods=['POST'])
def create_meter():
    """Crear medidor"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        data = request.get_json() or {}
        meter = UtilityMasterService.save_meter(data)
        if not meter:
            return jsonify({
                'message': 'No se pudo crear. Se requiere unit_id, code y valid_from',
                'success': False}), 400
        return jsonify({'message': 'Medidor creado exitosamente',
                        'success': True, 'data': meter}), 201
    except Exception as ex:
        return server_error('create_meter', ex)


@main.route('/meters/<int:meter_id>', methods=['PUT'])
def update_meter(meter_id):
    """Actualizar medidor"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        data = request.get_json() or {}
        meter = UtilityMasterService.save_meter(data, meter_id=meter_id)
        if not meter:
            return jsonify({
                'message': 'Medidor no encontrado o rango de vigencia inválido',
                'success': False}), 400
        return ok(meter, 'Medidor actualizado exitosamente')
    except Exception as ex:
        return server_error('update_meter', ex)


@main.route('/meters/replace', methods=['POST'])
def replace_meter():
    """Cambiar el medidor de un departamento.

    Cierra la vigencia del medidor actual y abre la del nuevo en la misma fecha,
    de modo que el consumo del periodo sume ambos tramos.
    """
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        data = request.get_json() or {}
        result = UtilityMasterService.replace_meter(
            unit_id=data.get('unit_id'),
            old_meter_id=data.get('old_meter_id'),
            new_code=data.get('new_code'),
            change_date=data.get('change_date'))
        if not result:
            return jsonify({
                'message': 'No se pudo cambiar. Se requiere unit_id, old_meter_id, '
                           'new_code y change_date válidos',
                'success': False}), 400
        return ok(result, 'Medidor reemplazado exitosamente')
    except Exception as ex:
        return server_error('replace_meter', ex)


@main.route('/meters/<int:meter_id>', methods=['DELETE'])
def delete_meter(meter_id):
    """Deshabilitar medidor"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        if not UtilityMasterService.delete_meter(meter_id):
            return jsonify({'message': 'Medidor no encontrado', 'success': False}), 404
        return jsonify({'message': 'Medidor deshabilitado exitosamente',
                        'success': True}), 200
    except Exception as ex:
        return server_error('delete_meter', ex)


# ---------------------------------------------------------------------------
# Lecturas
# ---------------------------------------------------------------------------

@main.route('/readings', methods=['GET'])
def get_readings():
    """Listar lecturas"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        readings = UtilityMasterService.get_readings(
            period=request.args.get('period'),
            meter_id=request.args.get('meter_id', type=int),
            unit_id=request.args.get('unit_id', type=int))
        return ok(readings, 'Lecturas obtenidas exitosamente', count=True)
    except Exception as ex:
        return server_error('get_readings', ex)


@main.route('/readings/sheet/<period>', methods=['GET'])
def get_reading_sheet(period):
    """Planilla de lecturas del periodo, con la lectura anterior precargada"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        rows = UtilityMasterService.get_reading_sheet(period)
        return ok(rows, 'Planilla de lecturas obtenida exitosamente', count=True)
    except Exception as ex:
        return server_error('get_reading_sheet', ex)


@main.route('/readings', methods=['POST'])
def create_reading():
    """Registrar lectura. El consumo se calcula solo."""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        data = request.get_json() or {}
        reading = UtilityMasterService.save_reading(data)
        if not reading:
            return jsonify({
                'message': 'No se pudo registrar. Verifique que la lectura actual '
                           'no sea menor que la anterior',
                'success': False}), 400
        return jsonify({'message': 'Lectura registrada exitosamente',
                        'success': True, 'data': reading}), 201
    except Exception as ex:
        return server_error('create_reading', ex)


@main.route('/readings/bulk', methods=['POST'])
def create_readings_bulk():
    """Registrar varias lecturas de una vez (toma de lecturas del mes)"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        payload = request.get_json() or {}
        items = payload.get('readings', [])
        if not isinstance(items, list) or not items:
            return jsonify({'message': 'Se requiere una lista de lecturas',
                            'success': False}), 400

        saved, failed = [], []
        for item in items:
            result = UtilityMasterService.save_reading(item)
            if result:
                saved.append(result)
            else:
                failed.append(item)

        return jsonify({
            'message': '%d lecturas registradas, %d con error' % (len(saved), len(failed)),
            'success': True,
            'data': {'saved': saved, 'failed': failed},
            'count': len(saved)}), 200
    except Exception as ex:
        return server_error('create_readings_bulk', ex)


@main.route('/readings/<int:reading_id>', methods=['PUT'])
def update_reading(reading_id):
    """Actualizar lectura"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        data = request.get_json() or {}
        reading = UtilityMasterService.save_reading(data, reading_id=reading_id)
        if not reading:
            return jsonify({
                'message': 'Lectura no encontrada o valores inválidos',
                'success': False}), 400
        return ok(reading, 'Lectura actualizada exitosamente')
    except Exception as ex:
        return server_error('update_reading', ex)


@main.route('/readings/<int:reading_id>', methods=['DELETE'])
def delete_reading(reading_id):
    """Eliminar lectura"""
    try:
        if not Security.verify_token(request.headers):
            return unauthorized()
        if not UtilityMasterService.delete_reading(reading_id):
            return jsonify({'message': 'Lectura no encontrada', 'success': False}), 404
        return jsonify({'message': 'Lectura eliminada exitosamente', 'success': True}), 200
    except Exception as ex:
        return server_error('delete_reading', ex)
