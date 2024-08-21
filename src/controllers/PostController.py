from pathlib import Path
import traceback
from flask import Blueprint, request, jsonify
from src.models.PostModel import Post
from src.database.b2_connection import bucket

import datetime

# Security
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
     
@main.route('/create', methods=['POST'])
def add_post():
     has_access = Security.verify_token(request.headers) 
    
    #img= request.files['image']
     #   image= img.read()
     #   filename=img.filename
      #  print(filename)
      #  bucket.upload_bytes(data_bytes=image, file_name=filename)
            #response.as_dict()
    
     
     if has_access:
        try:
             
            title= request.json['title']
            slug= request.json['slug']
            description = request.json['description']
            
            file_name = "captura.png"
            file = Path(file_name).resolve()
            response=bucket.upload_local_file(local_file=file,file_name=file_name)
            response = response.as_dict()

          
            #file = image.read()

            image_url= bucket.get_download_url(response.get("fileName"))
            
            category_id= request.json['category_id']  
           # user_id= request.json['user_id'] 
            user_id =1
            published=request.json['published']
            created_at=datetime.datetime.utcnow()
            updated_at= datetime.datetime.utcnow() 

            _post = Post(0,title, slug, description,image_url, category_id, user_id,published, created_at, updated_at)            

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