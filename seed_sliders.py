#!/usr/bin/env python3
"""
Script para crear sliders de prueba usando la API
Uso: python seed_sliders.py
"""

import requests
import json
import sys

def create_test_sliders():
    """Crear 4 sliders de prueba usando la API"""
    
    print("=== Creando Sliders de Prueba ===")
    
    # 1. Login para obtener token
    login_url = "http://127.0.0.1:5000/api/auth/login"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        login_response = requests.post(login_url, json=login_data)
        if login_response.status_code != 200:
            print(f"Error en login: {login_response.status_code}")
            return False
        
        token = login_response.json()['token']
        print("✓ Token obtenido exitosamente")
        
        # Headers con autenticación
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # 2. Datos de sliders
        sliders_data = [
            {
                "title": "Desarrollo Web Profesional",
                "subtitle": "Creamos sitios web modernos y responsivos con las últimas tecnologías",
                "link": "https://amarutech.com/servicios/desarrollo-web",
                "image_url": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1200&h=600&fit=crop",
                "published": True,
                "sort_order": 1
            },
            {
                "title": "Aplicaciones Móviles",
                "subtitle": "Desarrollamos apps nativas e híbridas para iOS y Android",
                "link": "https://amarutech.com/servicios/apps-moviles",
                "image_url": "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=1200&h=600&fit=crop",
                "published": True,
                "sort_order": 2
            },
            {
                "title": "Consultoría Tecnológica",
                "subtitle": "Asesoramiento especializado para la transformación digital de tu empresa",
                "link": "https://amarutech.com/servicios/consultoria",
                "image_url": "https://images.unsplash.com/photo-1552664730-d307ca884978?w=1200&h=600&fit=crop",
                "published": True,
                "sort_order": 3
            },
            {
                "title": "Soporte y Mantenimiento",
                "subtitle": "Servicios de soporte 24/7 y mantenimiento continuo para tus proyectos",
                "link": "https://amarutech.com/servicios/soporte",
                "image_url": "https://images.unsplash.com/photo-1551434678-e076c223a692?w=1200&h=600&fit=crop",
                "published": True,
                "sort_order": 4
            }
        ]
        
        # 3. Crear sliders
        create_url = "http://127.0.0.1:5000/api/sliders/"
        created_count = 0
        
        for i, slider_data in enumerate(sliders_data, 1):
            print(f"Creando slider {i}: {slider_data['title']}")
            
            response = requests.post(create_url, json=slider_data, headers=headers)
            
            if response.status_code == 201:
                print(f"  ✓ Slider {i} creado exitosamente")
                created_count += 1
            else:
                result = response.json()
                print(f"  ✗ Error en slider {i}: {result['message']}")
        
        print(f"\n=== Resumen ===")
        print(f"Sliders creados exitosamente: {created_count}/4")
        
        # 4. Verificar sliders creados
        if created_count > 0:
            print(f"\n=== Verificación ===")
            list_response = requests.get("http://127.0.0.1:5000/api/sliders/list")
            
            if list_response.status_code == 200:
                data = list_response.json()
                print(f"Total de sliders públicos: {data['count']}")
                
                for i, slider in enumerate(data['data'], 1):
                    print(f"  {i}. {slider['title']} (orden: {slider['sort_order']})")
        
        return created_count == 4
        
    except requests.exceptions.ConnectionError:
        print("✗ Error: No se puede conectar al servidor. ¿Está ejecutándose la aplicación?")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    success = create_test_sliders()
    sys.exit(0 if success else 1)