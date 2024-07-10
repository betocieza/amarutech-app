from flask import Blueprint, request, jsonify
from src.models.UserModel import User

import datetime

# Security
from src.utils.Security import Security
# Services
from src.services.UserService import UserService

main = Blueprint('user_blueprint', __name__)

@main.route('/list', methods=['GET'])
def get_list_users():  
    try:
        users = UserService.get_list_users()
        if (len(users) > 0):
            return jsonify(users)
        else:
            return jsonify({'message': "NOTFOUND", 'success': True})
    except Exception as ex:
        return jsonify({'message': "ERROR", 'success': False})



@main.route('/all', methods=['GET'])
def get_users():   
    has_access = Security.verify_token(request.headers) 
    if has_access:
        try:
            users = UserService.get_users()
            if (len(users) > 0):
                return jsonify(users)
            else:
                return jsonify({'message': "NOTFOUND", 'success': True})
        except Exception as ex:
            return jsonify({'message': "ERROR", 'success': False})
    else:
        response = jsonify({'message': 'Unauthorized'})
        return response, 401
    

@main.route('/<user_id>', methods=['GET'])
def get_user_by_id(user_id):
     has_access = Security.verify_token(request.headers) 
     
     if has_access:
        try:
            user = UserService.getuserById(user_id)          
            if user!= None:
                return jsonify(user)
            else:
                return jsonify({'message': "NOTFOUND", 'success': True})
        except Exception as ex:
            return jsonify({'message': "ERROR", 'success': False})
     else:
        response = jsonify({'message': 'Unauthorized'})
        return response, 401
     
@main.route('/create', methods=['POST'])
def add_user():
     has_access = Security.verify_token(request.headers)     
     if has_access:
        try:
             
            title= request.json['title']
            subtitle= request.json['subtitle']
            link = request.json['link']
            image_url= request.json['image_url']
            published=request.json['published']
            created_at=datetime.datetime.utcnow()
            updated_at= datetime.datetime.utcnow() 

            _user = User(0,title,subtitle,link,image_url,published,created_at,updated_at)            

            if UserService.saveuser(_user):
                return jsonify({'message':"user add successfully",'success': True})
            else:
                return jsonify({'message': "NOTFOUND", 'success': True})
        except Exception as ex:
            return jsonify({'message': "Error in server", 'success': False})
     else:
        response = jsonify({'message': 'Unauthorized'})
        return response, 401
     
@main.route('/update/<user_id>', methods=['PUT'])
def update_user(user_id):
    has_access = Security.verify_token(request.headers) 
    
    if has_access:
        try:            
            title= request.json['title']
            subtitle= request.json['subtitle']
            link = request.json['link']
            image_url= request.json['image_url'] 
            published=request.json['published']
            updated_at= datetime.datetime.utcnow() 

            user = User(0,title,subtitle,link,image_url,published,0, updated_at)             

            if UserService.updateuser(user_id, user):
                return jsonify({'message':"user updated success",'success': True})
            else:
                return jsonify({'message': "NOTFOUND", 'success': True})
        except Exception as ex:
            return jsonify({'message': "ERROR", 'success': False})
    else:
        response = jsonify({'message': 'Unauthorized'})
        return response, 401