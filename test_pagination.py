#!/usr/bin/env python3
"""
Script para probar la paginación de posts
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from src.services.PostService import PostService
from src.models.PostEntity import Post
import datetime

def test_pagination():
    """Prueba la paginación de posts"""
    
    print("=== Prueba de Paginacion de Posts ===")
    
    # Crear algunos posts de prueba si no existen
    print("\n1. Verificando posts existentes...")
    try:
        all_posts = PostService.get_all_posts()
        print(f"Posts existentes: {len(all_posts)}")
        
        # Si hay menos de 5 posts, crear algunos para probar paginación
        if len(all_posts) < 5:
            print("\n2. Creando posts de prueba para paginación...")
            for i in range(5 - len(all_posts)):
                test_post = Post(
                    post_id=0,
                    title=f"Post de Prueba Paginacion {i+1}",
                    slug=f"post-prueba-paginacion-{i+1}",
                    description=f"Descripción del post de prueba número {i+1} para probar paginación",
                    category_id=1,
                    user_id=1,
                    published=True,
                    created_at=datetime.datetime.now(),
                    updated_at=datetime.datetime.now(),
                    image_url=None,
                    tags=[f'prueba-{i+1}', 'paginacion']
                )
                
                result = PostService.savePost(test_post)
                print(f"  - Post {i+1} creado: {result}")
    
    except Exception as e:
        print(f"Error verificando/creando posts: {e}")
    
    # Probar paginación
    print("\n3. Probando paginación...")
    
    # Página 1 con 2 posts por página
    print("\n3.1. Página 1 (2 posts por página):")
    try:
        result_page1 = PostService.get_posts(page=1, per_page=2)
        if result_page1:
            print(f"  - Posts en página 1: {len(result_page1['posts'])}")
            print(f"  - Total de posts: {result_page1['pagination']['total']}")
            print(f"  - Total de páginas: {result_page1['pagination']['pages']}")
            print(f"  - Página actual: {result_page1['pagination']['page']}")
            print(f"  - Tiene siguiente: {result_page1['pagination']['has_next']}")
            
            if result_page1['posts']:
                print(f"  - Primer post: {result_page1['posts'][0]['title']}")
        else:
            print("  - Error: No se obtuvo resultado")
    except Exception as e:
        print(f"  - Error en página 1: {e}")
    
    # Página 2 con 2 posts por página
    print("\n3.2. Página 2 (2 posts por página):")
    try:
        result_page2 = PostService.get_posts(page=2, per_page=2)
        if result_page2:
            print(f"  - Posts en página 2: {len(result_page2['posts'])}")
            print(f"  - Página actual: {result_page2['pagination']['page']}")
            print(f"  - Tiene anterior: {result_page2['pagination']['has_prev']}")
            print(f"  - Tiene siguiente: {result_page2['pagination']['has_next']}")
            
            if result_page2['posts']:
                print(f"  - Primer post: {result_page2['posts'][0]['title']}")
        else:
            print("  - Error: No se obtuvo resultado")
    except Exception as e:
        print(f"  - Error en página 2: {e}")
    
    # Probar parámetros inválidos
    print("\n3.3. Probando parámetros inválidos:")
    try:
        # Página 0 (debería convertirse a 1)
        result_invalid = PostService.get_posts(page=0, per_page=3)
        if result_invalid:
            print(f"  - Página 0 -> Página {result_invalid['pagination']['page']}")
        
        # Per_page muy grande (debería limitarse a 100)
        result_big = PostService.get_posts(page=1, per_page=200)
        if result_big:
            print(f"  - Per_page 200 -> {result_big['pagination']['per_page']}")
            
    except Exception as e:
        print(f"  - Error en parámetros inválidos: {e}")
    
    # Comparar con método sin paginación
    print("\n4. Comparando con método sin paginación:")
    try:
        all_posts = PostService.get_all_posts()
        paginated_result = PostService.get_posts(page=1, per_page=100)
        
        print(f"  - get_all_posts(): {len(all_posts)} posts")
        if paginated_result:
            print(f"  - get_posts() total: {paginated_result['pagination']['total']} posts")
            print(f"  - Coinciden: {len(all_posts) == paginated_result['pagination']['total']}")
    except Exception as e:
        print(f"  - Error comparando métodos: {e}")
    
    print("\n=== Pruebas de Paginación Completadas ===")

if __name__ == "__main__":
    test_pagination()