from src.database import db
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List

class PostEntity(db.Model):
    __tablename__ = 'posts'
    
    post_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    published = db.Column(db.Boolean, default=False)
    tags = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'post_id': self.post_id,
            'title': self.title,
            'slug': self.slug,
            'description': self.description,
            'image_url': self.image_url,
            'category_id': self.category_id,
            'user_id': self.user_id,
            'published': self.published,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# DTO Classes moved from PostModel
@dataclass
class Post:
    post_id: Optional[int]
    title: str
    slug: str
    description: str    
    category_id: int
    user_id: int
    published: bool
    created_at: datetime
    updated_at: datetime
    image_url: Optional[str] = None  # Puede ser None si no hay imagen
    tags: Optional[List[str]] = None  # Lista de tags

    def to_json(self):
        return {        
            'post_id': self.post_id,
            'title': self.title,
            'slug': self.slug,
            'description': self.description,                     
            'category_id': self.category_id,
            'user_id': self.user_id,
            'published': self.published,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else None,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else None,
            'image_url': self.image_url,
            'tags': self.tags if self.tags else []
        }

class PostMonth():
    def __init__(self, monthName, numberPosts) -> None:
        self.monthName = monthName
        self.numberPosts = numberPosts
     
    def to_json(self):
        return {        
           'monthName': self.monthName ,
           'numberPosts':self.numberPosts,
        } 

class PostCategory():
    def __init__(self, category_id, numberPostsByCategory) -> None:
        self.category_id = category_id
        self.numberPostsByCategory = numberPostsByCategory
    
    def to_json(self):
        return {        
           'category_id': self.category_id ,
           'numberPostsByCategory':self.numberPostsByCategory,
        }
