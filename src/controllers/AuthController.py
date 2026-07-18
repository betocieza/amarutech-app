from flask import Blueprint, request, jsonify
import secrets
import traceback
from datetime import datetime, timedelta

from decouple import config

# Logger
from src.utils.Logger import Logger
# Models
from src.models.UserEntity import UserEntity, User
from src.database import db
# Security
from src.utils.Security import Security
# Services
from src.services.AuthService import AuthService
# Mailer
from src.utils.Mailer import Mailer

main = Blueprint('auth_blueprint', __name__)

RESET_TOKEN_TTL_MINUTES = 60


@main.route('/login', methods=['POST'])
def login():
    try:
        # Validar que el request tenga contenido JSON
        if not request.is_json:
            return jsonify({
                'message': 'Content-Type debe ser application/json',
                'success': False
            }), 400
        
        data = request.get_json()
        
        # Validar que los campos requeridos estén presentes
        if not data:
            return jsonify({
                'message': 'Datos JSON requeridos',
                'success': False
            }), 400
        
        # Obtener credenciales - puede ser username o email
        login_field = data.get('username') or data.get('email')
        password = data.get('password')
        
        # Validar que ambos campos estén presentes
        if not login_field or not password:
            return jsonify({
                'message': 'Username/email y password son requeridos',
                'success': False
            }), 400
        
        # Validar que no estén vacíos
        if not login_field.strip() or not password.strip():
            return jsonify({
                'message': 'Username/email y password no pueden estar vacíos',
                'success': False
            }), 400
        
        # Buscar usuario por username o email usando ORM
        user_entity = None
        
        # Determinar si es email o username
        if '@' in login_field:
            # Es un email
            user_entity = UserEntity.query.filter_by(email=login_field.strip().lower()).first()
        else:
            # Es un username
            user_entity = UserEntity.query.filter_by(username=login_field.strip()).first()
        
        # Verificar si el usuario existe
        if not user_entity:
            Logger.add_to_log("warning", f"Intento de login fallido: usuario no encontrado - {login_field}")
            return jsonify({
                'message': 'Credenciales inválidas',
                'success': False
            }), 401
        
        # Verificar si el usuario está habilitado
        if not user_entity.enabled:
            Logger.add_to_log("warning", f"Intento de login con usuario deshabilitado: {login_field}")
            return jsonify({
                'message': 'Usuario deshabilitado',
                'success': False
            }), 401
        
        # Verificar la contraseña
        if not user_entity.check_password(password):
            Logger.add_to_log("warning", f"Intento de login fallido: contraseña incorrecta - {login_field}")
            return jsonify({
                'message': 'Credenciales inválidas',
                'success': False
            }), 401
        
        # Crear objeto User para el token
        authenticated_user = User(
            user_id=user_entity.user_id,
            first_name=user_entity.first_name,
            last_name=user_entity.last_name,
            email=user_entity.email,
            username=user_entity.username,
            password=None,  # No incluir password en el token
            enabled=user_entity.enabled
        )
        
        # Generar token JWT
        encoded_token = Security.generate_token(authenticated_user)
        
        Logger.add_to_log("info", f"Login exitoso para usuario: {user_entity.username}")
        
        return jsonify({
            'message': 'Login exitoso',
            'token': encoded_token,
            'success': True,
            'user': {
                'user_id': user_entity.user_id,
                'username': user_entity.username,
                'email': user_entity.email,
                'first_name': user_entity.first_name,
                'last_name': user_entity.last_name,
                'enabled': user_entity.enabled
            }
        }), 200
        
    except KeyError as ke:
        Logger.add_to_log("error", f"Campo faltante en el JSON: {str(ke)}")
        return jsonify({
            'message': f'Campo requerido faltante: {str(ke)}',
            'success': False
        }), 400
        
    except Exception as ex:
        Logger.add_to_log("error", f"Error en login: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500


@main.route('/validate-token', methods=['POST'])
def validate_token():
    """Endpoint para validar si un token JWT es válido"""
    try:
        # Obtener token del header Authorization
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'message': 'Token de autorización requerido',
                'valid': False
            }), 401
        
        # Verificar formato Bearer
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'message': 'Formato de token inválido. Use: Bearer <token>',
                'valid': False
            }), 401
        
        token = auth_header.split(' ')[1]
        
        # Validar token
        payload = Security.verify_token(token)
        
        if payload:
            return jsonify({
                'message': 'Token válido',
                'valid': True,
                'user': payload
            }), 200
        else:
            return jsonify({
                'message': 'Token inválido o expirado',
                'valid': False
            }), 401
            
    except Exception as ex:
        Logger.add_to_log("error", f"Error validando token: {str(ex)}")
        return jsonify({
            'message': 'Error interno del servidor',
            'valid': False
        }), 500


@main.route('/refresh-token', methods=['POST'])
def refresh_token():
    """Endpoint para refrescar un token JWT"""
    try:
        # Obtener token del header Authorization
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'message': 'Token de autorización requerido',
                'success': False
            }), 401
        
        token = auth_header.split(' ')[1]
        
        # Verificar token actual
        payload = Security.verify_token(token)
        
        if not payload:
            return jsonify({
                'message': 'Token inválido o expirado',
                'success': False
            }), 401
        
        # Buscar usuario actual en base de datos
        user_entity = UserEntity.query.get(payload['user_id'])
        
        if not user_entity or not user_entity.enabled:
            return jsonify({
                'message': 'Usuario no encontrado o deshabilitado',
                'success': False
            }), 401
        
        # Crear nuevo objeto User
        user = User(
            user_id=user_entity.user_id,
            first_name=user_entity.first_name,
            last_name=user_entity.last_name,
            email=user_entity.email,
            username=user_entity.username,
            password=None,
            enabled=user_entity.enabled
        )
        
        # Generar nuevo token
        new_token = Security.generate_token(user)
        
        return jsonify({
            'message': 'Token renovado exitosamente',
            'token': new_token,
            'success': True
        }), 200
        
    except Exception as ex:
        Logger.add_to_log("error", f"Error refrescando token: {str(ex)}")
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500


@main.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Genera un token de reseteo y envía el email con el enlace"""
    try:
        if not request.is_json:
            return jsonify({
                'message': 'Content-Type debe ser application/json',
                'success': False
            }), 400

        data = request.get_json()
        email = (data or {}).get('email', '').strip().lower()

        if not email:
            return jsonify({
                'message': 'El email es requerido',
                'success': False
            }), 400

        generic_response = {
            'message': 'Si el email existe, se ha enviado un enlace de recuperación',
            'success': True
        }

        user_entity = UserEntity.query.filter_by(email=email).first()

        # Respuesta genérica siempre, para no filtrar qué emails existen
        if not user_entity or not user_entity.enabled:
            return jsonify(generic_response), 200

        token = secrets.token_urlsafe(32)
        user_entity.reset_token = token
        user_entity.reset_token_expires_at = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_TTL_MINUTES)
        db.session.commit()

        frontend_url = config('FRONTEND_URL', default='http://localhost:4200')
        reset_url = f"{frontend_url}/api/auth/reset-password?token={token}"

        sent = Mailer.send_password_reset_email(user_entity.email, reset_url)
        if not sent:
            Logger.add_to_log("error", f"No se pudo enviar el email de reseteo a {email}")

        Logger.add_to_log("info", f"Solicitud de reseteo de contraseña para: {email}")

        return jsonify(generic_response), 200

    except Exception as ex:
        Logger.add_to_log("error", f"Error en forgot-password: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500


@main.route('/reset-password', methods=['POST'])
def reset_password():
    """Valida el token de reseteo y establece la nueva contraseña"""
    try:
        if not request.is_json:
            return jsonify({
                'message': 'Content-Type debe ser application/json',
                'success': False
            }), 400

        data = request.get_json()
        token = (data or {}).get('token', '').strip()
        new_password = (data or {}).get('password', '')

        if not token or not new_password:
            return jsonify({
                'message': 'Token y nueva contraseña son requeridos',
                'success': False
            }), 400

        if len(new_password) < 8:
            return jsonify({
                'message': 'La contraseña debe tener al menos 8 caracteres',
                'success': False
            }), 400

        user_entity = UserEntity.query.filter_by(reset_token=token).first()

        if not user_entity or not user_entity.reset_token_expires_at:
            return jsonify({
                'message': 'Enlace de recuperación inválido o expirado',
                'success': False
            }), 400

        if datetime.utcnow() > user_entity.reset_token_expires_at:
            return jsonify({
                'message': 'Enlace de recuperación inválido o expirado',
                'success': False
            }), 400

        user_entity.set_password(new_password)
        user_entity.reset_token = None
        user_entity.reset_token_expires_at = None
        db.session.commit()

        Logger.add_to_log("info", f"Contraseña restablecida para usuario: {user_entity.username}")

        return jsonify({
            'message': 'Contraseña restablecida exitosamente',
            'success': True
        }), 200

    except Exception as ex:
        Logger.add_to_log("error", f"Error en reset-password: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500