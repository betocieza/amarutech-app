import traceback
# SQLAlchemy
from src.models.CategoryEntity import CategoryEntity
from src.database import db
# Logger
from src.utils.Logger import Logger
# Models
from src.models.CategoryEntity import Category


class CategoryService():

# Methods for admin  
    @classmethod
    def get_categories(cls):
        try:
            categories = []
            # Obtener todas las categorías ordenadas por fecha de creación
            category_entities = CategoryEntity.query.order_by(CategoryEntity.created_at).all()
            
            for category_entity in category_entities:
                category = Category(
                    category_id=category_entity.category_id,
                    name=category_entity.name,
                    created_at=category_entity.created_at,
                    updated_at=category_entity.updated_at
                )
                categories.append(category.to_json())
            return categories
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return []

    @classmethod
    def getCategoryById(cls, category_id):
        try:
            category_entity = CategoryEntity.query.get(category_id)
            if category_entity:
                return category_entity.to_dict()
            return None
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None
    
    # Method for insert new Category
    @classmethod
    def saveCategory(cls, category):
        try:
            new_category = CategoryEntity(
                name=category.name
            )
            db.session.add(new_category)
            db.session.commit()
            return "Category add success"
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return "Error adding category"

    # Method for update Category
    @classmethod
    def updateCategory(cls, category_id, category):
        try:
            category_entity = CategoryEntity.query.get(category_id)
            if category_entity:
                category_entity.name = category.name
                
                db.session.commit()
                return "Category updated successfully"
            return "Category not found"
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return "Error updating category"
