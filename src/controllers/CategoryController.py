from flask import Blueprint, request, jsonify
from src.models.CategoryModel import Category

import datetime

# Security
from src.utils.Security import Security
# Services
from src.services.CategoryService import CategoryService

main = Blueprint('category_blueprint', __name__)



@main.route('/all', methods=['GET'])
def get_categories():   
    has_access = Security.verify_token(request.headers) 
    if has_access:
        try:
            categories = CategoryService.get_categories()
            if (len(categories) > 0):
                return jsonify(categories)
            else:
                return jsonify({'message': "NOTFOUND", 'success': True})
        except Exception as ex:
            return jsonify({'message': "ERROR", 'success': False})
    else:
        response = jsonify({'message': 'Unauthorized'})
        return response, 401
    

@main.route('/<category_id>', methods=['GET'])
def get_category_by_id(category_id):
     has_access = Security.verify_token(request.headers) 
     
     if has_access:
        try:
            category = CategoryService.getCategoryById(category_id)          
            if category!= None:
                return jsonify(category)
            else:
                return jsonify({'message': "NOTFOUND", 'success': True})
        except Exception as ex:
            return jsonify({'message': "ERROR", 'success': False})
     else:
        response = jsonify({'message': 'Unauthorized'})
        return response, 401
     
@main.route('/create', methods=['POST'])
def add_category():
     has_access = Security.verify_token(request.headers)     
     if has_access:
        try:
             
            name= request.json['name']
            created_at=datetime.datetime.utcnow()
            updated_at= datetime.datetime.utcnow() 

            _category = Category(0,name, created_at, updated_at)            

            if CategoryService.saveCategory(_category):
                return jsonify({'message':"category add success",'success': True})
            else:
                return jsonify({'message': "NOTFOUND", 'success': True})
        except Exception as ex:
            return jsonify({'message': "Error in server", 'success': False})
     else:
        response = jsonify({'message': 'Unauthorized'})
        return response, 401
     
@main.route('/update/<category_id>', methods=['PUT'])
def update_category(category_id):
    has_access = Security.verify_token(request.headers) 
    
    if has_access:
        try:            
            name= request.json['name']
            updated_at= datetime.datetime.utcnow() 
            category = Category(0,name,0, updated_at)             

            if CategoryService.updateCategory(category_id, category):
                return jsonify({'message':"Category updated successfully",'success': True})
            else:
                return jsonify({'message': "NOTFOUND", 'success': True})
        except Exception as ex:
            return jsonify({'message': "ERROR", 'success': False})
    else:
        response = jsonify({'message': 'Unauthorized'})
        return response, 401