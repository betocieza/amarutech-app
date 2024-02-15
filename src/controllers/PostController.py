from flask import Blueprint, request, jsonify
from src.models.PostModel import Post

import datetime

# Security
from src.utils.Security import Security
# Services
from src.services.PostService import PostService

main = Blueprint('post_blueprint', __name__)

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
    
     if has_access:
        try:
             
            title= request.json['title']
            slug= request.json['slug']
            description = request.json['description']
            image_url= request.json['image_url'] 
            author_id= request.json['author_id'] 
            published=request.json['published']
            created_at=datetime.datetime.utcnow()
            updated_at= datetime.datetime.utcnow() 

            _post = Post(0,title, slug, description,image_url, author_id,published, created_at, updated_at)            

            if PostService.savePost(_post):
                return jsonify("Post add success")
            else:
                return jsonify({'message': "NOTFOUND", 'success': True})
        except Exception as ex:
            return jsonify({'message': "ERROR", 'success': False})
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
            author_id= request.json['author_id'] 
            published=request.json['published']
            updated_at= datetime.datetime.utcnow() 

            post = Post(0,title, slug, description,image_url, author_id, published,0, updated_at)             

            if PostService.updatePost(post_id, post):
                return jsonify(" success")
            else:
                return jsonify({'message': "NOTFOUND", 'success': True})
        except Exception as ex:
            return jsonify({'message': "ERROR", 'success': False})
    else:
        response = jsonify({'message': 'Unauthorized'})
        return response, 401