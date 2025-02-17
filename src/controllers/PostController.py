from pathlib import Path
import traceback
from flask import Blueprint, request, jsonify
from src.models.PostModel import Post
from src.database.b2_connection import bucket
from werkzeug.utils import secure_filename
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
            posts = PostService.get_posts()
            if (len(posts) > 0):
                return jsonify(posts)
            else:
                return jsonify({'message': "NOTFOUND", 'success': True})
        except Exception as ex:
            return jsonify({'message': "ERROR", 'success': False})
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
def  upload_file():
    try:
        file= request.files['file']
        image=file.read()
        file_name =file.filename
        
        response=bucket.upload_bytes(data_bytes=image,file_name=file_name)
        response = response.as_dict()
        url= bucket.get_download_url(response.get("fileName"))
        print(url)
        return "Upload successfuly"
    except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return jsonify({'message': "Error in server", 'success': False})

@main.route('/create', methods=['POST'])
def add_post():
     has_access = Security.verify_token(request.headers) 
     if has_access:
        try:
            
            title = request.form.get('title')
            slug = request.form.get('slug')
            description = request.form.get('description')
            category_id = request.form.get('category_id',1)
            user_id = 1  # Se puede cambiar por el usuario autenticado
            published = request.form.get('published', 'false').lower() == 'true'
            created_at = datetime.datetime.utcnow()
            updated_at = datetime.datetime.utcnow()          
             # Verificar si se envió un archivo
            image_url = None
            if 'image' in request.files:
                image_file = request.files['image']
                image_url = upload_to_backblaze(image_file)

                if not image_url:
                    return jsonify({'message': 'Error al subir la imagen', 'success': False}), 500
            _post = Post(0,title, slug, description,category_id, user_id,published, created_at, updated_at,image_url)            

            if PostService.savePost(_post):
                return jsonify({'message':"Post add success",'success': True})
            else:
                return jsonify({'message': "NOTFOUND", 'success': True})
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return jsonify({'message': "Error in server", 'success': False})
     else:
        response = jsonify({'message': 'Unauthorized'})
        return response, 401
     
@main.route('/update/<post_id>', methods=['PUT'])
def update_post(post_id):
    has_access = Security.verify_token(request.headers) 
    
    if has_access:
        try:            
            title= request.json['title']
            slug= request.json['slug']
            description = request.json['description']
            image_url= request.json['image_url'] 
            category_id = request.json['category_id']
            user_id= 1 
            published=request.json['published']
            updated_at= datetime.datetime.utcnow() 

            post = Post(0,title, slug, description,image_url,category_id, user_id, published,0, updated_at)             

            if PostService.updatePost(post_id, post):
                return jsonify({'message':"Post updated success",'success': True})
            else:
                return jsonify({'message': "NOTFOUND", 'success': True})
        except Exception as ex:
            return jsonify({'message': "ERROR", 'success': False})
    else:
        response = jsonify({'message': 'Unauthorized'})
        return response, 401