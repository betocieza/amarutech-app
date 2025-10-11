import traceback
import json
from datetime import datetime
# SQLAlchemy
from src.models.PostEntity import PostEntity
from src.database import db
from sqlalchemy import func, extract
# Logger
from src.utils.Logger import Logger
# Models
from src.models.PostEntity import Post, PostCategory, PostMonth


class PostService():
# Methods for front web
 
    @classmethod
    def get_list_posts(cls):
        try:
            posts = []
            # Obtener posts publicados de categoría 1, ordenados por fecha, límite 4
            post_entities = PostEntity.query.filter_by(
                published=True, 
                category_id=1
            ).order_by(PostEntity.created_at.desc()).limit(4).all()
            
            for post_entity in post_entities:
                # Manejar tags como lista JSON
                tags = post_entity.tags if post_entity.tags else []
                if isinstance(tags, str):
                    try:
                        tags = json.loads(tags)
                    except:
                        tags = []
                
                post = Post(
                    post_id=post_entity.post_id,
                    title=post_entity.title,
                    slug=post_entity.slug,
                    description=post_entity.description,
                    category_id=post_entity.category_id,
                    user_id=post_entity.user_id,
                    published=post_entity.published,
                    created_at=post_entity.created_at,
                    updated_at=post_entity.updated_at,
                    image_url=post_entity.image_url,
                    tags=tags
                )
                posts.append(post.to_json())
            return posts
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return []


    @classmethod
    def get_list_news(cls):
        try:
            posts = []
            # Obtener posts publicados de categoría 2, ordenados por fecha, límite 4
            post_entities = PostEntity.query.filter_by(
                published=True, 
                category_id=2
            ).order_by(PostEntity.created_at.desc()).limit(4).all()
            
            for post_entity in post_entities:
                # Manejar tags como lista JSON
                tags = post_entity.tags if post_entity.tags else []
                if isinstance(tags, str):
                    try:
                        tags = json.loads(tags)
                    except:
                        tags = []
                
                post = Post(
                    post_id=post_entity.post_id,
                    title=post_entity.title,
                    slug=post_entity.slug,
                    description=post_entity.description,
                    category_id=post_entity.category_id,
                    user_id=post_entity.user_id,
                    published=post_entity.published,
                    created_at=post_entity.created_at,
                    updated_at=post_entity.updated_at,
                    image_url=post_entity.image_url,
                    tags=tags
                )
                posts.append(post.to_json())
            return posts
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return []

# Methods for admin  
    @classmethod
    def get_posts_by_month(cls):
        try:
            posts = []
            # Agrupar posts por mes usando SQLAlchemy
            results = db.session.query(
                func.to_char(PostEntity.created_at, 'MON').label('monthName'),
                func.count(PostEntity.post_id).label('numberPosts')
            ).group_by(
                func.to_char(PostEntity.created_at, 'MON')
            ).order_by(
                func.to_char(PostEntity.created_at, 'MON').asc()
            ).all()
            
            for row in results:
                post = PostMonth(row.monthName, row.numberPosts)
                posts.append(post.to_json())
            return posts
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return []

    @classmethod
    def get_posts_by_category(cls):
        try:
            posts = []
            # Agrupar posts por categoría usando SQLAlchemy
            results = db.session.query(
                PostEntity.category_id.label('category'),
                func.count(PostEntity.post_id).label('numberPost')
            ).group_by(PostEntity.category_id).all()
            
            for row in results:
                post = PostCategory(row.category, row.numberPost)
                posts.append(post.to_json())
            return posts
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return []
            return posts
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())

    @classmethod
    def get_posts(cls, page=1, per_page=10):
        try:
            # Validar parámetros de paginación
            page = max(1, int(page)) if page else 1
            per_page = max(1, min(100, int(per_page))) if per_page else 10  # Límite máximo de 100 por página
            
            # Usar SQLAlchemy ORM con paginación
            pagination = PostEntity.query.order_by(PostEntity.created_at.desc()).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            posts = []
            for post_entity in pagination.items:
                # Manejar tags como lista JSON
                tags = post_entity.tags if post_entity.tags else []
                if isinstance(tags, str):
                    try:
                        tags = json.loads(tags)
                    except:
                        tags = []
                
                # Crear objeto Post con los datos del ORM
                post = Post(
                    post_id=post_entity.post_id,
                    title=post_entity.title,
                    slug=post_entity.slug,
                    description=post_entity.description,
                    category_id=post_entity.category_id,
                    user_id=post_entity.user_id,
                    published=post_entity.published,
                    created_at=post_entity.created_at,
                    updated_at=post_entity.updated_at,
                    image_url=post_entity.image_url,
                    tags=tags
                )
                posts.append(post.to_json())
            
            # Retornar datos con información de paginación
            return {
                'posts': posts,
                'pagination': {
                    'page': pagination.page,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'prev_num': pagination.prev_num,
                    'has_next': pagination.has_next,
                    'next_num': pagination.next_num
                }
            }
            
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return {
                'posts': [],
                'pagination': {
                    'page': 1,
                    'per_page': per_page,
                    'total': 0,
                    'pages': 0,
                    'has_prev': False,
                    'prev_num': None,
                    'has_next': False,
                    'next_num': None
                }
            }

    @classmethod
    def get_all_posts(cls):
        """
        Método de compatibilidad que retorna solo la lista de posts sin paginación
        Para mantener compatibilidad con código existente
        """
        try:
            result = cls.get_posts(page=1, per_page=1000)  # Obtener muchos posts
            return result['posts'] if result else []
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            return []



    @classmethod
    def getPostById(cls, post_id):
        try:
            post_entity = PostEntity.query.get(post_id)
            if post_entity:
                # Convertir el entity a dict y manejar tags
                post_dict = post_entity.to_dict()
                # Manejar tags como lista JSON
                if 'tags' in post_dict and post_dict['tags']:
                    if isinstance(post_dict['tags'], str):
                        try:
                            post_dict['tags'] = json.loads(post_dict['tags'])
                        except:
                            post_dict['tags'] = []
                else:
                    post_dict['tags'] = []
                return post_dict
            return None
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None
    
    # Method for insert new Post
    @classmethod
    def savePost(cls, post):
        try:
            # Convertir tags a JSON string si es una lista
            tags_json = None
            if hasattr(post, 'tags') and post.tags:
                if isinstance(post.tags, list):
                    tags_json = json.dumps(post.tags)
                elif isinstance(post.tags, str):
                    tags_json = post.tags
            
            new_post = PostEntity(
                title=post.title,
                slug=post.slug,
                description=post.description,
                image_url=post.image_url,
                category_id=post.category_id,
                user_id=post.user_id,
                published=post.published,
                tags=tags_json
            )
            db.session.add(new_post)
            db.session.commit()
            return "Post add success"
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return "Error adding post"
            return "Error adding post"

    # Method for update Post
    @classmethod
    def updatePost(cls, post_id, post):
        try:
            post_entity = PostEntity.query.get(post_id)
            if not post_entity:
                return "Post not found"
            
            # Validar campos requeridos
            if not post.title or not post.title.strip():
                return "Title is required"
            
            if not post.slug or not post.slug.strip():
                return "Slug is required"
                
            if not post.description or not post.description.strip():
                return "Description is required"
                
            if not post.category_id:
                return "Category ID is required"
            
            # Convertir tags a JSON string si es una lista
            tags_json = None
            if hasattr(post, 'tags') and post.tags:
                if isinstance(post.tags, list):
                    tags_json = json.dumps(post.tags)
                elif isinstance(post.tags, str):
                    tags_json = post.tags
            
            # Actualizar solo campos válidos
            post_entity.title = post.title.strip()
            post_entity.slug = post.slug.strip()
            post_entity.description = post.description.strip()
            post_entity.category_id = post.category_id
            post_entity.published = post.published
            post_entity.tags = tags_json
            
            # Solo actualizar image_url si se proporciona
            if hasattr(post, 'image_url') and post.image_url is not None:
                post_entity.image_url = post.image_url
            
            # Solo actualizar user_id si se proporciona y es válido
            if hasattr(post, 'user_id') and post.user_id:
                post_entity.user_id = post.user_id
            
            post_entity.updated_at = datetime.utcnow()
            
            db.session.commit()
            return "Post updated successfully"
            
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return "Error updating post"
