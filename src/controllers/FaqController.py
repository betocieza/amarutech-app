from flask import Blueprint, request, jsonify
import traceback

# Logger
from src.utils.Logger import Logger
# Models
from src.models.FaqEntity import Faq
# Services
from src.services.FaqService import FaqService

main = Blueprint('faq_blueprint', __name__)

@main.route('/list', methods=['GET'])
def get_faqs():
    """Obtener todas las FAQs públicas (habilitadas)"""
    try:
        category = request.args.get('category')  # Parámetro opcional para filtrar por categoría
        faqs = FaqService.get_faqs(category=category, enabled_only=True)
        
        return jsonify({
            'message': 'FAQs obtenidas exitosamente',
            'success': True,
            'data': faqs,
            'count': len(faqs)
        }), 200
        
    except Exception as ex:
        Logger.add_to_log("error", f"Error obteniendo FAQs: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500

@main.route('/all', methods=['GET'])
def get_all_faqs():
    """Obtener todas las FAQs (para administración) - incluye deshabilitadas"""
    try:
        category = request.args.get('category')
        faqs = FaqService.get_faqs(category=category, enabled_only=False)
        
        return jsonify({
            'message': 'FAQs obtenidas exitosamente',
            'success': True,
            'data': faqs,
            'count': len(faqs)
        }), 200
        
    except Exception as ex:
        Logger.add_to_log("error", f"Error obteniendo FAQs admin: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500

@main.route('/category/<category>', methods=['GET'])
def get_faqs_by_category(category):
    """Obtener FAQs por categoría específica"""
    try:
        faqs = FaqService.get_faqs_by_category(category, enabled_only=True)
        
        return jsonify({
            'message': f'FAQs de categoría {category} obtenidas exitosamente',
            'success': True,
            'data': faqs,
            'count': len(faqs),
            'category': category
        }), 200
        
    except Exception as ex:
        Logger.add_to_log("error", f"Error obteniendo FAQs por categoría: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500

@main.route('/<int:faq_id>', methods=['GET'])
def get_faq_by_id(faq_id):
    """Obtener una FAQ específica por ID"""
    try:
        faq = FaqService.get_faq_by_id(faq_id)
        
        if faq:
            return jsonify({
                'message': 'FAQ obtenida exitosamente',
                'success': True,
                'data': faq
            }), 200
        else:
            return jsonify({
                'message': 'FAQ no encontrada',
                'success': False
            }), 404
            
    except Exception as ex:
        Logger.add_to_log("error", f"Error obteniendo FAQ por ID: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500

@main.route('/', methods=['POST'])
def create_faq():
    """Crear una nueva FAQ"""
    try:
        if not request.is_json:
            return jsonify({
                'message': 'Content-Type debe ser application/json',
                'success': False
            }), 400

        data = request.get_json()
        
        # Validar campos requeridos
        if not data or not data.get('question') or not data.get('answer'):
            return jsonify({
                'message': 'Question y answer son campos requeridos',
                'success': False
            }), 400

        # Crear objeto FAQ
        faq = Faq(
            faq_id=None,
            question=data['question'].strip(),
            answer=data['answer'].strip(),
            category=data.get('category', 'general'),
            enabled=data.get('enabled', True),
            sort_order=data.get('sort_order', 0)
        )

        result = FaqService.save_faq(faq)
        
        if "exitosamente" in result:
            return jsonify({
                'message': result,
                'success': True
            }), 201
        else:
            return jsonify({
                'message': result,
                'success': False
            }), 500

    except Exception as ex:
        Logger.add_to_log("error", f"Error creando FAQ: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500

@main.route('/<int:faq_id>', methods=['PUT'])
def update_faq(faq_id):
    """Actualizar una FAQ existente"""
    try:
        if not request.is_json:
            return jsonify({
                'message': 'Content-Type debe ser application/json',
                'success': False
            }), 400

        data = request.get_json()
        
        # Validar campos requeridos
        if not data or not data.get('question') or not data.get('answer'):
            return jsonify({
                'message': 'Question y answer son campos requeridos',
                'success': False
            }), 400

        # Crear objeto FAQ
        faq = Faq(
            faq_id=faq_id,
            question=data['question'].strip(),
            answer=data['answer'].strip(),
            category=data.get('category', 'general'),
            enabled=data.get('enabled', True),
            sort_order=data.get('sort_order', 0)
        )

        result = FaqService.update_faq(faq_id, faq)
        
        if "exitosamente" in result:
            return jsonify({
                'message': result,
                'success': True
            }), 200
        elif "no encontrada" in result:
            return jsonify({
                'message': result,
                'success': False
            }), 404
        else:
            return jsonify({
                'message': result,
                'success': False
            }), 500

    except Exception as ex:
        Logger.add_to_log("error", f"Error actualizando FAQ: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500

@main.route('/<int:faq_id>', methods=['DELETE'])
def delete_faq(faq_id):
    """Eliminar una FAQ"""
    try:
        result = FaqService.delete_faq(faq_id)
        
        if "exitosamente" in result:
            return jsonify({
                'message': result,
                'success': True
            }), 200
        elif "no encontrada" in result:
            return jsonify({
                'message': result,
                'success': False
            }), 404
        else:
            return jsonify({
                'message': result,
                'success': False
            }), 500

    except Exception as ex:
        Logger.add_to_log("error", f"Error eliminando FAQ: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500

@main.route('/<int:faq_id>/toggle', methods=['PATCH'])
def toggle_faq_enabled(faq_id):
    """Cambiar el estado enabled de una FAQ"""
    try:
        result = FaqService.toggle_faq_enabled(faq_id)
        
        if "exitosamente" in result:
            return jsonify({
                'message': result,
                'success': True
            }), 200
        elif "no encontrada" in result:
            return jsonify({
                'message': result,
                'success': False
            }), 404
        else:
            return jsonify({
                'message': result,
                'success': False
            }), 500

    except Exception as ex:
        Logger.add_to_log("error", f"Error cambiando estado FAQ: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500

@main.route('/<int:faq_id>/sort-order', methods=['PATCH'])
def update_faq_sort_order(faq_id):
    """Actualizar el orden de una FAQ"""
    try:
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

        result = FaqService.update_faq_sort_order(faq_id, sort_order)
        
        if "exitosamente" in result:
            return jsonify({
                'message': result,
                'success': True
            }), 200
        elif "no encontrada" in result:
            return jsonify({
                'message': result,
                'success': False
            }), 404
        else:
            return jsonify({
                'message': result,
                'success': False
            }), 500

    except Exception as ex:
        Logger.add_to_log("error", f"Error actualizando orden FAQ: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500

@main.route('/seed', methods=['POST'])
def seed_default_faqs():
    """Poblar la base de datos con FAQs por defecto"""
    try:
        result = FaqService.seed_default_faqs()
        
        if "exitosamente" in result:
            return jsonify({
                'message': result,
                'success': True
            }), 201
        else:
            return jsonify({
                'message': result,
                'success': False
            }), 400

    except Exception as ex:
        Logger.add_to_log("error", f"Error creando FAQs por defecto: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500