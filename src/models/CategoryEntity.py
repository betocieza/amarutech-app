from src.database import db
from datetime import datetime

class CategoryEntity(db.Model):
    __tablename__ = 'categories'
    
    category_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con posts
    posts = db.relationship('PostEntity', backref='category', lazy=True)
    
    def to_dict(self):
        return {
            'category_id': self.category_id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# DTO Class moved from CategoryModel
class Category():
    def __init__(self, category_id, name, created_at, updated_at) -> None:
        self.category_id = category_id
        self.name = name
        self.created_at = created_at
        self.updated_at = updated_at

    def to_json(self):
        return {        
           'category_id': self.category_id ,
           'name':self.name,
           'created_at' : self.created_at,
           'updated_at': self.updated_at
        }
