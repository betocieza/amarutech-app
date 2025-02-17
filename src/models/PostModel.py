from dataclasses import dataclass
from typing import Optional
import datetime

@dataclass
class Post:
    post_id: Optional[int]
    title: str
    slug: str
    description: str    
    category_id: int
    user_id: int
    published: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    image_url: Optional[str] = None  # Puede ser None si no hay imagen

    def to_json(self):
        return {        
            'post_id': self.post_id,
            'title': self.title,
            'slug': self.slug,
            'description': self.description,                     
            'category_id': self.category_id,
            'user_id': self.user_id,
            'published': self.published,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime.datetime) else None,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime.datetime) else None,
            'image_url': self.image_url ,  
           
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