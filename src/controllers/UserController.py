from flask import Blueprint, request, jsonify
import re

# Security
from src.utils.Security import Security
# Services
from src.services.UserService import UserService
# Models
from src.models.UserEntity import User

main = Blueprint('user_blueprint', __name__)

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
MIN_PASSWORD = 6


def unauthorized():
    return jsonify({'message': 'Unauthorized', 'success': False}), 401


def read_user(data, require_password):
    """Valida el cuerpo de la petición y arma el DTO; devuelve (user, error)."""
    if not isinstance(data, dict):
        return None, "Cuerpo de la petición inválido"

    first_name = str(data.get('first_name') or '').strip()
    last_name = str(data.get('last_name') or '').strip()
    email = str(data.get('email') or '').strip().lower()
    username = str(data.get('username') or '').strip()
    password = str(data.get('password') or '')
    enabled = data.get('enabled', True)

    if not first_name or not last_name:
        return None, "El nombre y el apellido son requeridos"
    if not EMAIL_RE.match(email):
        return None, "Ingresa un email válido"
    if len(username) < 3:
        return None, "El usuario debe tener al menos 3 caracteres"
    if require_password or password:
        if len(password) < MIN_PASSWORD:
            return None, "La contraseña debe tener al menos %d caracteres" % MIN_PASSWORD

    return User(0, first_name, last_name, email, username, password or None, bool(enabled)), None


@main.route('/all', methods=['GET'])
def get_users():
    if not Security.verify_token(request.headers):
        return unauthorized()
    return jsonify(UserService.get_users())


@main.route('/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    if not Security.verify_token(request.headers):
        return unauthorized()
    user = UserService.getUserById(user_id)
    if user is None:
        return jsonify({'message': "Usuario no encontrado", 'success': False}), 404
    return jsonify({'success': True, 'message': 'OK', 'data': user})


@main.route('/create', methods=['POST'])
def add_user():
    if not Security.verify_token(request.headers):
        return unauthorized()

    user, error = read_user(request.get_json(silent=True), require_password=True)
    if error:
        return jsonify({'message': error, 'success': False}), 400

    ok, message, data = UserService.saveUser(user)
    if not ok:
        return jsonify({'message': message, 'success': False}), 400
    return jsonify({'message': message, 'success': True, 'data': data}), 201


@main.route('/update/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    if not Security.verify_token(request.headers):
        return unauthorized()

    user, error = read_user(request.get_json(silent=True), require_password=False)
    if error:
        return jsonify({'message': error, 'success': False}), 400

    ok, message = UserService.updateUser(user_id, user)
    return jsonify({'message': message, 'success': ok}), 200 if ok else 400


@main.route('/delete/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if not Security.verify_token(request.headers):
        return unauthorized()

    ok, message = UserService.deleteUser(user_id)
    return jsonify({'message': message, 'success': ok}), 200 if ok else 400
