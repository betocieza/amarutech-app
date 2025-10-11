#!/usr/bin/env python3
"""
Script para probar la actualización de posts y verificar que los campos requeridos se manejen correctamente.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.PostService import PostService
from src.models.PostEntity import Post
import datetime

def test_post_update():
    """Prueba la actualización de posts con diferentes escenarios"""
    
    print("=== Prueba de Actualización de Posts ===")
    
    # Primero obtener un post existente
    print("\n1. Obteniendo posts existentes...")
    posts = PostService.getPosts()
    
    if not posts or len(posts) == 0:
        print("❌ No hay posts para probar")
        return False
    
    # Tomar el primer post para pruebas
    test_post_id = posts[0]['post_id']
    print(f"✅ Usando post ID: {test_post_id}")
    
    # Obtener el post actual
    current_post = PostService.getPostById(test_post_id)
    if not current_post:
        print("❌ No se pudo obtener el post actual")
        return False
        
    print(f"✅ Post actual: {current_post['title']}")
    
    # Prueba 1: Actualización válida
    print("\n2. Prueba 1: Actualización válida...")
    try:
        updated_post = Post(
            post_id=0,
            title="Título Actualizado - Test",
            slug="titulo-actualizado-test", 
            description="Descripción actualizada para prueba",
            category_id=current_post['category_id'],
            user_id=current_post['user_id'],
            published=True,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
            image_url=current_post.get('image_url'),
            tags=['test', 'actualización']
        )
        
        result = PostService.updatePost(test_post_id, updated_post)
        print(f"✅ Resultado: {result}")
        
        # Verificar que se actualizó
        updated = PostService.getPostById(test_post_id)
        if updated and updated['title'] == "Título Actualizado - Test":
            print("✅ Actualización exitosa verificada")
        else:
            print("❌ La actualización no se reflejó correctamente")
            
    except Exception as e:
        print(f"❌ Error en prueba 1: {e}")
    
    # Prueba 2: Intento de actualización con título vacío (debería fallar)
    print("\n3. Prueba 2: Actualización con título vacío...")
    try:
        invalid_post = Post(
            post_id=0,
            title="",  # Título vacío
            slug="slug-vacio",
            description="Descripción",
            category_id=current_post['category_id'],
            user_id=current_post['user_id'],
            published=False,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
            image_url=None,
            tags=[]
        )
        
        result = PostService.updatePost(test_post_id, invalid_post)
        if "Title is required" in result:
            print(f"✅ Validación correcta: {result}")
        else:
            print(f"❌ Debería haber fallado: {result}")
            
    except Exception as e:
        print(f"❌ Error en prueba 2: {e}")
    
    # Prueba 3: Actualización con None en campos (debería fallar)
    print("\n4. Prueba 3: Actualización con campos None...")
    try:
        none_post = Post(
            post_id=0,
            title=None,  # Título None
            slug=None,   # Slug None
            description=None,  # Descripción None
            category_id=None,  # Category None
            user_id=current_post['user_id'],
            published=False,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
            image_url=None,
            tags=[]
        )
        
        result = PostService.updatePost(test_post_id, none_post)
        if "required" in result:
            print(f"✅ Validación correcta para campos None: {result}")
        else:
            print(f"❌ Debería haber fallado con campos None: {result}")
            
    except Exception as e:
        print(f"❌ Error en prueba 3: {e}")
    
    # Restaurar el post original
    print("\n5. Restaurando post original...")
    try:
        original_post = Post(
            post_id=0,
            title=current_post['title'],
            slug=current_post['slug'],
            description=current_post['description'],
            category_id=current_post['category_id'],
            user_id=current_post['user_id'],
            published=current_post['published'],
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
            image_url=current_post.get('image_url'),
            tags=current_post.get('tags', [])
        )
        
        result = PostService.updatePost(test_post_id, original_post)
        print(f"✅ Post restaurado: {result}")
        
    except Exception as e:
        print(f"❌ Error al restaurar: {e}")
    
    print("\n=== Pruebas de Actualización Completadas ===")
    return True

if __name__ == "__main__":
    test_post_update()