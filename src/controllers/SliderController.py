from flask import Blueprint, request, jsonify
import traceback
import datetime

# Logger
from src.utils.Logger import Logger
# Models
from src.models.SliderEntity import SliderEntity, Slider
# Security
from src.utils.Security import Security
# Services
from src.services.SliderService import SliderService

main = Blueprint('slider_blueprint', __name__)


@main.route('/list', methods=['GET'])
def get_list_sliders():
    """Obtener todos los sliders habilitados para público"""
    try:
        sliders = SliderService.get_list_sliders()
        return jsonify({
            'message': 'Sliders obtenidos exitosamente',
            'success': True,
            'data': sliders,
            'count': len(sliders)
        }), 200
    except Exception as ex:
        Logger.add_to_log("error", f"Error obteniendo sliders públicos: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500


@main.route('/all', methods=['GET'])
def get_sliders():
    """Obtener todos los sliders (admin) - requiere autenticación"""
    try:
        # Verificar autenticación
        has_access = Security.verify_token(request.headers)
        if not has_access:
            return jsonify({
                'message': 'No autorizado',
                'success': False
            }), 401
        
        sliders = SliderService.get_sliders()
        return jsonify({
            'message': 'Sliders obtenidos exitosamente',
            'success': True,
            'data': sliders,
            'count': len(sliders)
        }), 200
        
    except Exception as ex:
        Logger.add_to_log("error", f"Error obteniendo todos los sliders: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500


@main.route('/<int:slider_id>', methods=['GET'])
def get_slider_by_id(slider_id):
    """Obtener slider por ID - requiere autenticación"""
    try:
        # Verificar autenticación
        has_access = Security.verify_token(request.headers)
        if not has_access:
            return jsonify({
                'message': 'No autorizado',
                'success': False
            }), 401
        
        # Validar ID
        if slider_id <= 0:
            return jsonify({
                'message': 'ID de slider inválido',
                'success': False
            }), 400
        
        slider = SliderService.getSliderById(slider_id)
        
        if slider:
            return jsonify({
                'message': 'Slider encontrado',
                'success': True,
                'data': slider
            }), 200
        else:
            return jsonify({
                'message': 'Slider no encontrado',
                'success': False
            }), 404
            
    except Exception as ex:
        Logger.add_to_log("error", f"Error obteniendo slider {slider_id}: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500


@main.route('/create', methods=['POST'])
def create_slider():
    """Crear nuevo slider - requiere autenticación"""
    try:
        # Verificar autenticación
        has_access = Security.verify_token(request.headers)
        if not has_access:
            return jsonify({
                'message': 'No autorizado',
                'success': False
            }), 401
        
        # Validar Content-Type
        if not request.is_json:
            return jsonify({
                'message': 'Content-Type debe ser application/json',
                'success': False
            }), 400
        
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['title', 'subtitle', 'link', 'image_url']
        for field in required_fields:
            if not data.get(field) or not data[field].strip():
                return jsonify({
                    'message': f'El campo {field} es requerido',
                    'success': False
                }), 400
        
        # Crear objeto Slider
        slider = Slider(
            slider_id=None,
            title=data['title'].strip(),
            subtitle=data['subtitle'].strip(),
            link=data['link'].strip(),
            image_url=data['image_url'].strip(),
            published=data.get('published', True),
            sort_order=data.get('sort_order', 0),
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow()
        )
        
        result = SliderService.saveSlider(slider)
        
        if "success" in result.lower():
            Logger.add_to_log("info", f"Slider creado exitosamente: {data['title']}")
            return jsonify({
                'message': 'Slider creado exitosamente',
                'success': True
            }), 201
        else:
            return jsonify({
                'message': result,
                'success': False
            }), 400
            
    except KeyError as ke:
        Logger.add_to_log("error", f"Campo faltante al crear slider: {str(ke)}")
        return jsonify({
            'message': f'Campo requerido faltante: {str(ke)}',
            'success': False
        }), 400
        
    except Exception as ex:
        Logger.add_to_log("error", f"Error creando slider: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500


@main.route('/update/<int:slider_id>', methods=['PUT'])
def update_slider(slider_id):
    """Actualizar slider existente - requiere autenticación"""
    try:
        # Verificar autenticación
        has_access = Security.verify_token(request.headers)
        if not has_access:
            return jsonify({
                'message': 'No autorizado',
                'success': False
            }), 401
        
        # Validar ID
        if slider_id <= 0:
            return jsonify({
                'message': 'ID de slider inválido',
                'success': False
            }), 400
        
        # Validar Content-Type
        if not request.is_json:
            return jsonify({
                'message': 'Content-Type debe ser application/json',
                'success': False
            }), 400
        
        data = request.get_json()
        
        # Validar que el slider existe
        existing_slider = SliderService.getSliderById(slider_id)
        if not existing_slider:
            return jsonify({
                'message': 'Slider no encontrado',
                'success': False
            }), 404
        
        # Validar datos requeridos
        required_fields = ['title', 'subtitle', 'link', 'image_url']
        for field in required_fields:
            if not data.get(field) or not data[field].strip():
                return jsonify({
                    'message': f'El campo {field} es requerido',
                    'success': False
                }), 400
        
        # Crear objeto Slider para actualización
        slider = Slider(
            slider_id=slider_id,
            title=data['title'].strip(),
            subtitle=data['subtitle'].strip(),
            link=data['link'].strip(),
            image_url=data['image_url'].strip(),
            published=data.get('published', True),
            sort_order=data.get('sort_order', 0),
            created_at=None,  # No se actualiza
            updated_at=datetime.datetime.utcnow()
        )
        
        result = SliderService.updateSlider(slider_id, slider)
        
        if "success" in result.lower():
            Logger.add_to_log("info", f"Slider {slider_id} actualizado exitosamente")
            return jsonify({
                'message': 'Slider actualizado exitosamente',
                'success': True
            }), 200
        else:
            return jsonify({
                'message': result,
                'success': False
            }), 400
            
    except KeyError as ke:
        Logger.add_to_log("error", f"Campo faltante al actualizar slider {slider_id}: {str(ke)}")
        return jsonify({
            'message': f'Campo requerido faltante: {str(ke)}',
            'success': False
        }), 400
        
    except Exception as ex:
        Logger.add_to_log("error", f"Error actualizando slider {slider_id}: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500


@main.route('/delete/<int:slider_id>', methods=['DELETE'])
def delete_slider(slider_id):
    """Eliminar slider - requiere autenticación"""
    try:
        # Verificar autenticación
        has_access = Security.verify_token(request.headers)
        if not has_access:
            return jsonify({
                'message': 'No autorizado',
                'success': False
            }), 401
        
        # Validar ID
        if slider_id <= 0:
            return jsonify({
                'message': 'ID de slider inválido',
                'success': False
            }), 400
        
        # Validar que el slider existe
        existing_slider = SliderService.getSliderById(slider_id)
        if not existing_slider:
            return jsonify({
                'message': 'Slider no encontrado',
                'success': False
            }), 404
        
        # Aquí podrías implementar SliderService.deleteSlider(slider_id)
        # Por ahora devolvemos un mensaje indicando que no está implementado
        return jsonify({
            'message': 'Funcionalidad de eliminación no implementada',
            'success': False
        }), 501
        
    except Exception as ex:
        Logger.add_to_log("error", f"Error eliminando slider {slider_id}: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500


@main.route('/toggle/<int:slider_id>', methods=['PATCH'])
def toggle_slider_status(slider_id):
    """Cambiar estado published del slider - requiere autenticación"""
    try:
        # Verificar autenticación
        has_access = Security.verify_token(request.headers)
        if not has_access:
            return jsonify({
                'message': 'No autorizado',
                'success': False
            }), 401
        
        # Validar ID
        if slider_id <= 0:
            return jsonify({
                'message': 'ID de slider inválido',
                'success': False
            }), 400
        
        # Validar que el slider existe
        existing_slider = SliderService.getSliderById(slider_id)
        if not existing_slider:
            return jsonify({
                'message': 'Slider no encontrado',
                'success': False
            }), 404
        
        # Aquí podrías implementar SliderService.toggleSliderStatus(slider_id)
        # Por ahora devolvemos un mensaje indicando que no está implementado
        return jsonify({
            'message': 'Funcionalidad de toggle no implementada',
            'success': False
        }), 501
        
    except Exception as ex:
        Logger.add_to_log("error", f"Error cambiando estado del slider {slider_id}: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500


@main.route('/<int:slider_id>/sort-order', methods=['PATCH'])
def update_slider_sort_order(slider_id):
    """Actualizar el orden de un slider - requiere autenticación"""
    try:
        # Verificar autenticación
        has_access = Security.verify_token(request.headers)
        if not has_access:
            return jsonify({
                'message': 'No autorizado',
                'success': False
            }), 401
        
        # Validar ID
        if slider_id <= 0:
            return jsonify({
                'message': 'ID de slider inválido',
                'success': False
            }), 400
        
        # Validar Content-Type
        if not request.is_json:
            return jsonify({
                'message': 'Content-Type debe ser application/json',
                'success': False
            }), 400

        data = request.get_json()
        sort_order = data.get('sort_order')
        
        if sort_order is None:
            return jsonify({
                'message': 'sort_order es requerido',
                'success': False
            }), 400

        # Validar que el slider existe
        existing_slider = SliderService.getSliderById(slider_id)
        if not existing_slider:
            return jsonify({
                'message': 'Slider no encontrado',
                'success': False
            }), 404

        # Crear objeto Slider con solo el sort_order actualizado
        slider = Slider(
            slider_id=slider_id,
            title=existing_slider['title'],
            subtitle=existing_slider['subtitle'],
            link=existing_slider['link'],
            image_url=existing_slider['image_url'],
            published=existing_slider['published'],
            sort_order=sort_order,
            created_at=None,
            updated_at=datetime.datetime.utcnow()
        )

        result = SliderService.updateSlider(slider_id, slider)
        
        if "successfully" in result.lower():
            Logger.add_to_log("info", f"Sort order del slider {slider_id} actualizado a {sort_order}")
            return jsonify({
                'message': 'Orden del slider actualizado exitosamente',
                'success': True
            }), 200
        else:
            return jsonify({
                'message': result,
                'success': False
            }), 400
        
    except Exception as ex:
        Logger.add_to_log("error", f"Error actualizando orden del slider {slider_id}: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500