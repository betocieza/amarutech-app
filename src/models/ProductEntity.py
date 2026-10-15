import json
from src.database import db
from datetime import datetime


class ProductEntity(db.Model):
    __tablename__ = 'products'

    product_id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    tagline = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(50), nullable=True)  # Nombre del icono del front (ej. 'pill', 'eye')
    tags = db.Column(db.String(500), nullable=True)  # Lista serializada como JSON
    image_url = db.Column(db.String(500), nullable=True)  # Captura del producto (Backblaze)
    link = db.Column(db.String(500), nullable=True)
    published = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_tags(self):
        if not self.tags:
            return []
        try:
            tags = json.loads(self.tags)
            return tags if isinstance(tags, list) else []
        except (ValueError, TypeError):
            return []

    def set_tags(self, tags):
        self.tags = json.dumps(tags or [], ensure_ascii=False)

    def to_dict(self):
        return {
            'product_id': self.product_id,
            'slug': self.slug,
            'name': self.name,
            'tagline': self.tagline,
            'description': self.description,
            'icon': self.icon,
            'tags': self.get_tags(),
            'image_url': self.image_url,
            'link': self.link,
            'published': self.published,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
