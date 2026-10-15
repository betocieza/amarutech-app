from flask import Blueprint, request, jsonify
import json
import re
import traceback

# Logger
from src.utils.Logger import Logger
# Security
from src.utils.Security import Security
# Services
from src.services.ProductService import ProductService
from src.services.UploadImage import upload_to_backblaze

main = Blueprint('product_blueprint', __name__)


def unauthorized():
    return jsonify({'message': 'No autorizado', 'success': False}), 401


def slugify(text):
    text = text.lower().strip()
    for src, dst in (('áàäâã', 'a'), ('éèëê', 'e'), ('íìïî', 'i'), ('óòöôõ', 'o'), ('úùüû', 'u'), ('ñ', 'n')):
        text = re.sub(f'[{src}]', dst, text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    return re.sub(r'[\s-]+', '-', text).strip('-')


def parse_tags(raw):
    """Acepta JSON ('["a","b"]') o texto separado por comas ('a, b')."""
    if not raw:
        return []
    raw = raw.strip()
    if raw.startswith('['):
        try:
            tags = json.loads(raw)
            return [str(tag).strip() for tag in tags if str(tag).strip()]
        except ValueError:
            pass
    return [tag.strip() for tag in raw.split(',') if tag.strip()]


def read_product_form(form, partial=False):
    """Convierte el multipart del admin en un dict para ProductService.
    Con partial=True solo incluye los campos enviados (update)."""
    data = {}
    for field in ('name', 'slug', 'tagline', 'description', 'icon', 'link'):
        if field in form:
            data[field] = (form.get(field) or '').strip() or None
    if 'tags' in form:
        data['tags'] = parse_tags(form.get('tags'))
    if 'published' in form:
        data['published'] = form.get('published', 'true').lower() == 'true'
    if 'sort_order' in form:
        try:
            data['sort_order'] = int(form.get('sort_order') or 0)
        except ValueError:
            data['sort_order'] = 0
    if not partial:
        data.setdefault('published', True)
        data.setdefault('sort_order', 0)
    return data


def upload_image_if_present(data):
    """Sube 'image' a Backblaze si viene en la petición. Devuelve un mensaje de error o None."""
    image_file = request.files.get('image')
    if image_file and image_file.filename:
        upload_result = upload_to_backblaze(image_file)
        if not upload_result['success']:
            return f'Error al subir la imagen: {upload_result["message"]}'
        data['image_url'] = upload_result['file_url']
    return None


@main.route('/list', methods=['GET'])
def get_list_products():
    """Productos publicados para la web pública"""
    try:
        products = ProductService.get_list_products()
        return jsonify({
            'message': 'Productos obtenidos exitosamente',
            'success': True,
            'data': products,
            'count': len(products)
        }), 200
    except Exception as ex:
        Logger.add_to_log("error", f"Error obteniendo productos públicos: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({'message': 'Error interno del servidor', 'success': False}), 500


@main.route('/all', methods=['GET'])
def get_products():
    """Todos los productos (admin) - requiere autenticación"""
    if not Security.verify_token(request.headers):
        return unauthorized()
    products = ProductService.get_products()
    return jsonify({
        'message': 'Productos obtenidos exitosamente',
        'success': True,
        'data': products,
        'count': len(products)
    }), 200


@main.route('/<int:product_id>', methods=['GET'])
def get_product_by_id(product_id):
    if not Security.verify_token(request.headers):
        return unauthorized()
    product = ProductService.get_product_by_id(product_id)
    if not product:
        return jsonify({'message': 'Producto no encontrado', 'success': False}), 404
    return jsonify({'message': 'Producto encontrado', 'success': True, 'data': product}), 200


@main.route('/create', methods=['POST'])
def create_product():
    """Crear producto (multipart/form-data, imagen opcional en 'image')"""
    if not Security.verify_token(request.headers):
        return unauthorized()
    try:
        data = read_product_form(request.form)

        if not data.get('name'):
            return jsonify({'message': 'El nombre es requerido', 'success': False}), 400

        data['slug'] = slugify(data.get('slug') or data['name'])
        if ProductService.slug_exists(data['slug']):
            return jsonify({'message': f'Ya existe un producto con el slug "{data["slug"]}"', 'success': False}), 400

        error = upload_image_if_present(data)
        if error:
            return jsonify({'message': error, 'success': False}), 400

        product = ProductService.save_product(data)
        if not product:
            return jsonify({'message': 'Error al guardar el producto', 'success': False}), 500

        Logger.add_to_log("info", f"Producto creado: {product['name']}")
        return jsonify({'message': 'Producto creado exitosamente', 'success': True, 'data': product}), 201

    except Exception as ex:
        Logger.add_to_log("error", f"Error creando producto: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({'message': 'Error interno del servidor', 'success': False}), 500


@main.route('/update/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Actualizar producto (multipart/form-data). 'image' reemplaza la imagen;
    remove_image=true la quita."""
    if not Security.verify_token(request.headers):
        return unauthorized()
    try:
        if not ProductService.get_product_by_id(product_id):
            return jsonify({'message': 'Producto no encontrado', 'success': False}), 404

        data = read_product_form(request.form, partial=True)

        if 'name' in data and not data['name']:
            return jsonify({'message': 'El nombre es requerido', 'success': False}), 400

        if 'slug' in data:
            data['slug'] = slugify(data['slug'] or data.get('name') or '')
            if not data['slug']:
                return jsonify({'message': 'El slug es requerido', 'success': False}), 400
            if ProductService.slug_exists(data['slug'], exclude_id=product_id):
                return jsonify({'message': f'Ya existe un producto con el slug "{data["slug"]}"', 'success': False}), 400

        if request.form.get('remove_image', 'false').lower() == 'true':
            data['image_url'] = None

        error = upload_image_if_present(data)
        if error:
            return jsonify({'message': error, 'success': False}), 400

        product = ProductService.update_product(product_id, data)
        if not product:
            return jsonify({'message': 'Error al actualizar el producto', 'success': False}), 500

        Logger.add_to_log("info", f"Producto {product_id} actualizado")
        return jsonify({'message': 'Producto actualizado exitosamente', 'success': True, 'data': product}), 200

    except Exception as ex:
        Logger.add_to_log("error", f"Error actualizando producto {product_id}: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({'message': 'Error interno del servidor', 'success': False}), 500


@main.route('/delete/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    if not Security.verify_token(request.headers):
        return unauthorized()
    if ProductService.delete_product(product_id):
        Logger.add_to_log("info", f"Producto {product_id} eliminado")
        return jsonify({'message': 'Producto eliminado exitosamente', 'success': True}), 200
    return jsonify({'message': 'Producto no encontrado', 'success': False}), 404
