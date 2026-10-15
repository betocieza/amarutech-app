import traceback
# SQLAlchemy
from src.models.ProductEntity import ProductEntity
from src.database import db
# Logger
from src.utils.Logger import Logger

# Campos editables desde el admin
PRODUCT_FIELDS = ('slug', 'name', 'tagline', 'description', 'icon', 'image_url', 'link', 'published', 'sort_order')


class ProductService():
# Methods for front web

    @classmethod
    def get_list_products(cls):
        try:
            product_entities = ProductEntity.query.filter_by(
                published=True
            ).order_by(ProductEntity.sort_order.asc(), ProductEntity.created_at.asc()).all()
            return [product.to_dict() for product in product_entities]
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return []

# Methods for admin
    @classmethod
    def get_products(cls):
        try:
            product_entities = ProductEntity.query.order_by(
                ProductEntity.sort_order.asc(), ProductEntity.created_at.asc()
            ).all()
            return [product.to_dict() for product in product_entities]
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return []

    @classmethod
    def get_product_by_id(cls, product_id):
        try:
            product_entity = ProductEntity.query.get(product_id)
            return product_entity.to_dict() if product_entity else None
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None

    @classmethod
    def slug_exists(cls, slug, exclude_id=None):
        query = ProductEntity.query.filter_by(slug=slug)
        if exclude_id:
            query = query.filter(ProductEntity.product_id != exclude_id)
        return query.first() is not None

    @classmethod
    def save_product(cls, data):
        """data: dict con PRODUCT_FIELDS + 'tags' (lista)"""
        try:
            product = ProductEntity(**{field: data.get(field) for field in PRODUCT_FIELDS})
            product.set_tags(data.get('tags'))
            db.session.add(product)
            db.session.commit()
            return product.to_dict()
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None

    @classmethod
    def update_product(cls, product_id, data):
        try:
            product = ProductEntity.query.get(product_id)
            if not product:
                return None
            for field in PRODUCT_FIELDS:
                if field in data:
                    setattr(product, field, data[field])
            if 'tags' in data:
                product.set_tags(data['tags'])
            db.session.commit()
            return product.to_dict()
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None

    @classmethod
    def delete_product(cls, product_id):
        try:
            product = ProductEntity.query.get(product_id)
            if not product:
                return False
            db.session.delete(product)
            db.session.commit()
            return True
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return False
