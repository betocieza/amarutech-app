from src.database import db
from datetime import datetime

class FaqEntity(db.Model):
    __tablename__ = 'faqs'
    
    faq_id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=True)  # 'consulting', 'general', etc.
    enabled = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)  # Para ordenar las preguntas
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'faq_id': self.faq_id,
            'question': self.question,
            'answer': self.answer,
            'category': self.category,
            'enabled': self.enabled,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# DTO Class for FAQ
class Faq():
    def __init__(self, faq_id, question, answer, category=None, enabled=True, sort_order=0, created_at=None, updated_at=None) -> None:
        self.faq_id = faq_id
        self.question = question
        self.answer = answer
        self.category = category
        self.enabled = enabled
        self.sort_order = sort_order
        self.created_at = created_at
        self.updated_at = updated_at

    def to_json(self):
        return {        
           'faq_id': self.faq_id,
           'question': self.question,
           'answer': self.answer,
           'category': self.category,
           'enabled': self.enabled,
           'sort_order': self.sort_order,
           'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
           'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }