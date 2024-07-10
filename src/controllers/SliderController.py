from flask import Blueprint, request, jsonify
from src.models.SliderModel import Slider

import datetime

# Security
from src.utils.Security import Security
# Services
from src.services.SliderService import SliderService

main = Blueprint('slider_blueprint', __name__)

@main.route('/list', methods=['GET'])
def get_list_sliders():  
    try:
        sliders = SliderService.get_list_sliders()
        if (len(sliders) > 0):
            return jsonify(sliders)
        else:
            return jsonify({'message': "NOTFOUND", 'success': True})
    except Exception as ex:
        return jsonify({'message': "ERROR", 'success': False})



@main.route('/all', methods=['GET'])
def get_sliders():   
    has_access = Security.verify_token(request.headers) 
    if has_access:
        try:
            sliders = SliderService.get_sliders()
            if (len(sliders) > 0):
                return jsonify(sliders)
            else:
                return jsonify({'message': "NOTFOUND", 'success': True})
        except Exception as ex:
            return jsonify({'message': "ERROR", 'success': False})
    else:
        response = jsonify({'message': 'Unauthorized'})
        return response, 401
    

@main.route('/<slider_id>', methods=['GET'])
def get_slider_by_id(slider_id):
     has_access = Security.verify_token(request.headers) 
     
     if has_access:
        try:
            slider = SliderService.getsliderById(slider_id)          
            if slider!= None:
                return jsonify(slider)
            else:
                return jsonify({'message': "NOTFOUND", 'success': True})
        except Exception as ex:
            return jsonify({'message': "ERROR", 'success': False})
     else:
        response = jsonify({'message': 'Unauthorized'})
        return response, 401
     
@main.route('/create', methods=['POST'])
def add_slider():
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

            _slider = Slider(0,title,subtitle,link,image_url,published,created_at,updated_at)            

            if SliderService.saveSlider(_slider):
                return jsonify({'message':"Slider add successfully",'success': True})
            else:
                return jsonify({'message': "NOTFOUND", 'success': True})
        except Exception as ex:
            return jsonify({'message': "Error in server", 'success': False})
     else:
        response = jsonify({'message': 'Unauthorized'})
        return response, 401
     
@main.route('/update/<slider_id>', methods=['PUT'])
def update_slider(slider_id):
    has_access = Security.verify_token(request.headers) 
    
    if has_access:
        try:            
            title= request.json['title']
            subtitle= request.json['subtitle']
            link = request.json['link']
            image_url= request.json['image_url'] 
            published=request.json['published']
            updated_at= datetime.datetime.utcnow() 

            slider = Slider(0,title,subtitle,link,image_url,published,0, updated_at)             

            if SliderService.updateSlider(slider_id, slider):
                return jsonify({'message':"Slider updated success",'success': True})
            else:
                return jsonify({'message': "NOTFOUND", 'success': True})
        except Exception as ex:
            return jsonify({'message': "ERROR", 'success': False})
    else:
        response = jsonify({'message': 'Unauthorized'})
        return response, 401