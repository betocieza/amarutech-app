from src.database import db
from datetime import datetime

class SliderEntity(db.Model):
    __tablename__ = 'sliders'
    
    slider_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    subtitle = db.Column(db.String(255), nullable=True)
    link = db.Column(db.String(500), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    published = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'slider_id': self.slider_id,
            'title': self.title,
            'subtitle': self.subtitle,
            'link': self.link,
            'image_url': self.image_url,
            'published': self.published,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# DTO Class moved from SliderModel
class Slider():
    def __init__(self, slider_id, title, subtitle, link, image_url, published, sort_order=0, created_at=None, updated_at=None) -> None:
        self.slider_id = slider_id
        self.title = title
        self.subtitle = subtitle
        self.link = link
        self.image_url = image_url
        self.published = published
        self.sort_order = sort_order
        self.created_at = created_at
        self.updated_at = updated_at

    def to_json(self):
        return {        
           'slider_id': self.slider_id ,
           'title':self.title,
           'subtitle': self.subtitle,
           'link':self.link,
           'image_url':self.image_url,
           'published': self.published,
           'sort_order': self.sort_order,
           'created_at' : self.created_at,
           'updated_at': self.updated_at
        }
