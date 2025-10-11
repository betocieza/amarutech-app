import traceback
from flask import Blueprint, request, jsonify
from src.models.PostEntity import Post
import datetime

# Security
from src.services.UploadImage import upload_to_backblaze
from src.utils.Logger import Logger
from src.utils.Security import Security
# Services
from src.services.PostService import PostService

main = Blueprint('post_blueprint', __name__)

@main.route('/list', methods=['GET'])
def get_list_posts():  
    try:
        posts = PostService.get_list_posts()
      
        if (len(posts) > 0):
            return jsonify(posts)
        else:
            return jsonify({'message': "NOTFOUND", 'success': True})
    except Exception as ex:
        return jsonify({'message': "ERROR", 'success': False})

@main.route('/news', methods=['GET'])
def get_list_news():  
    try:
        news = PostService.get_list_news()
        if (len(news) > 0):
            return jsonify(news)
        else:
            return jsonify({'message': "NOTFOUND", 'success': True})
    except Exception as ex:
        return jsonify({'message': "ERROR", 'success': False}) 

@main.route('/postsxmonth', methods=['GET'])
def get_posts_by_month():   
    has_access = Security.verify_token(request.headers) 
    if has_access:
        try:
            posts = PostService.get_posts_by_month()
            if (len(posts) > 0):
                return jsonify(posts)
            else:
                return jsonify({'message': "NOTFOUND", 'success': True})
        except Exception as ex:
            return jsonify({'message': "ERROR", 'success': False})
    else:
        response = jsonify({'message': 'Unauthorized'})
        return response, 401

@main.route('/postsxcategory', methods=['GET'])
def get_posts_by_category():   
    has_access = Security.verify_token(request.headers) 
    if has_access:
        try:
            posts = PostService.get_posts_by_category()
            if (len(posts) > 0):
                return jsonify(posts)
            else:
                return jsonify({'message': "NOTFOUND", 'success': True})
        except Exception as ex:
            return jsonify({'message': "ERROR", 'success': False})
    else:
        response = jsonify({'message': 'Unauthorized'})
        return response, 401
    
@main.route('/all', methods=['GET'])
def get_posts():   
    has_access = Security.verify_token(request.headers) 
    if has_access:
        try:
            # Obtener parámetros de paginación desde query params
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            
            # Obtener posts con paginación
            result = PostService.get_posts(page=page, per_page=per_page)
            
            if result and result['posts']:
                return jsonify({
                    'success': True,
                    'data': result['posts'],
                    'pagination': result['pagination']
                })
            else:
                return jsonify({
                    'success': True,
                    'message': "No posts found",
                    'data': [],
                    'pagination': result['pagination'] if result else None
                })
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return jsonify({'message': "Internal server error", 'success': False}), 500
    else:
        response = jsonify({'message': 'Unauthorized'})
        return response, 401

@main.route('/all/no-pagination', methods=['GET'])
def get_all_posts():   
    """Endpoint para obtener todos los posts sin paginación - compatibilidad"""
    has_access = Security.verify_token(request.headers) 
    if has_access:
        try:
            posts = PostService.get_all_posts()
            if posts and len(posts) > 0:
                return jsonify({
                    'success': True,
                    'data': posts,
                    'total': len(posts)
                })
            else:
                return jsonify({
                    'success': True,
                    'message': "No posts found",
                    'data': [],
                    'total': 0
                })
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return jsonify({'message': "Internal server error", 'success': False}), 500
    else:
        response = jsonify({'message': 'Unauthorized'})
        return response, 401
    

@main.route('/<post_id>', methods=['GET'])
def get_post_by_id(post_id):
     has_access = Security.verify_token(request.headers) 
     
     if has_access:
        try:
            post = PostService.getPostById(post_id)          
            if post!= None:
                return jsonify(post)
            else:
                return jsonify({'message': "NOTFOUND", 'success': True})
        except Exception as ex:
            return jsonify({'message': "ERROR", 'success': False})
     else:
        response = jsonify({'message': 'Unauthorized'})
        return response, 401
     
@main.route('/upload', methods=['POST'])
def upload_file():
    try:
        # Verificar si se envió un archivo
        if 'file' not in request.files:
            return jsonify({
                'message': 'No se encontró el archivo',
                'success': False
            }), 400
        
        file = request.files['file']
        
        # Usar el servicio mejorado de upload
        upload_result = upload_to_backblaze(file)
        
        if upload_result['success']:
            return jsonify({
                'message': 'Archivo subido exitosamente',
                'success': True,
                'url': upload_result['file_url'],
                'file_name': upload_result['filename']
            })
        else:
            return jsonify({
                'message': upload_result['message'],
                'success': False
            }), 400
            
    except Exception as ex:
        Logger.add_to_log("error", str(ex))
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({
            'message': "Error interno del servidor",
            'success': False
        }), 500

@main.route('/create', methods=['POST'])
def add_post():
    has_access = Security.verify_token(request.headers) 
    if has_access:
        try:
            title = request.form.get('title')
            slug = request.form.get('slug')
            description = request.form.get('description')
            category_id = request.form.get('category_id', 1)
            user_id = 1  # Se puede cambiar por el usuario autenticado
            published = request.form.get('published', 'false').lower() == 'true'
            created_at = datetime.datetime.utcnow()
            updated_at = datetime.datetime.utcnow()
            
            # Manejar tags - puede venir como string JSON o lista separada por comas
            tags = request.form.get('tags', '[]')
            if tags and tags != '[]':
                try:
                    # Si viene como JSON string
                    import json
                    if tags.startswith('[') and tags.endswith(']'):
                        tags = json.loads(tags)
                    else:
                        # Si viene como string separado por comas
                        tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
                except:
                    tags = []
            else:
                tags = []
            
            # Verificar si se envió un archivo de imagen
            image_url = None
            if 'image' in request.files:
                image_file = request.files['image']
                upload_result = upload_to_backblaze(image_file)
                
                if upload_result['success']:
                    image_url = upload_result['file_url']
                else:
                    return jsonify({
                        'message': f'Error al subir la imagen: {upload_result["message"]}', 
                        'success': False
                    }), 400
            
            _post = Post(0, title, slug, description, category_id, user_id, published, created_at, updated_at, image_url, tags)
            
            if PostService.savePost(_post):
                return jsonify({
                    'message': "Post creado exitosamente",
                    'success': True,
                    'image_url': image_url
                })
            else:
                return jsonify({
                    'message': "Error al guardar el post", 
                    'success': False
                }), 500
                
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return jsonify({
                'message': "Error interno del servidor", 
                'success': False
            }), 500
    else:
        return jsonify({
            'message': "Token de acceso inválido", 
            'success': False
        }), 401
     
@main.route('/update/<post_id>', methods=['PUT'])
def update_post(post_id):
    has_access = Security.verify_token(request.headers) 
    
    if has_access:
        try:
            # Obtener el post actual para preservar valores existentes
            current_post = PostService.getPostById(post_id)
            if not current_post:
                return jsonify({
                    'message': "Post no encontrado", 
                    'success': False
                }), 404
            
            # Usar form data para permitir envío de archivos
            # Solo actualizar campos que se envíen en la petición
            title = request.form.get('title', current_post['title'])
            slug = request.form.get('slug', current_post['slug'])
            description = request.form.get('description', current_post['description'])
            
            # Validar campos requeridos
            if not title or not title.strip():
                return jsonify({
                    'message': "El título es requerido", 
                    'success': False
                }), 400
                
            if not slug or not slug.strip():
                return jsonify({
                    'message': "El slug es requerido", 
                    'success': False
                }), 400
                
            if not description or not description.strip():
                return jsonify({
                    'message': "La descripción es requerida", 
                    'success': False
                }), 400
            
            # Manejar category_id con validación
            category_id_str = request.form.get('category_id')
            if category_id_str:
                try:
                    category_id = int(category_id_str)
                except ValueError:
                    return jsonify({
                        'message': "El ID de categoría debe ser un número válido", 
                        'success': False
                    }), 400
            else:
                category_id = current_post['category_id']
            
            user_id = current_post['user_id']  # Preservar el usuario original
            published = request.form.get('published', str(current_post['published'])).lower() == 'true'
            updated_at = datetime.datetime.utcnow()
            
            # Manejar tags - puede venir como string JSON o lista separada por comas
            tags = request.form.get('tags')
            if tags is not None:
                if tags == '[]' or tags == '':
                    tags = []
                else:
                    try:
                        # Si viene como JSON string
                        import json
                        if tags.startswith('[') and tags.endswith(']'):
                            tags = json.loads(tags)
                        else:
                            # Si viene como string separado por comas
                            tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
                    except:
                        tags = []
            else:
                # Preservar tags existentes si no se envían nuevos
                current_tags = current_post.get('tags', '[]')
                if current_tags and current_tags != '[]':
                    try:
                        import json
                        tags = json.loads(current_tags) if isinstance(current_tags, str) else current_tags
                    except:
                        tags = []
                else:
                    tags = []
            
            # Manejar la imagen - puede venir como archivo nuevo o URL existente
            image_url = request.form.get('image_url', current_post.get('image_url'))
            
            # Si se envía una nueva imagen, subirla a B2
            if 'image' in request.files and request.files['image'].filename:
                image_file = request.files['image']
                upload_result = upload_to_backblaze(image_file)
                
                if upload_result['success']:
                    image_url = upload_result['file_url']
                else:
                    return jsonify({
                        'message': f'Error al subir la nueva imagen: {upload_result["message"]}', 
                        'success': False
                    }), 400

            # Crear objeto Post con todos los valores validados
            post = Post(0, title.strip(), slug.strip(), description.strip(), category_id, user_id, published, 0, updated_at, image_url, tags)

            if PostService.updatePost(post_id, post):
                return jsonify({
                    'message': "Post actualizado exitosamente",
                    'success': True,
                    'image_url': image_url
                })
            else:
                return jsonify({
                    'message': "Post no encontrado", 
                    'success': False
                }), 404
                
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return jsonify({
                'message': "Error interno del servidor", 
                'success': False
            }), 500
    else:
        return jsonify({
            'message': "Token de acceso inválido", 
            'success': False
        }), 401