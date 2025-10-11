from src.database import db
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

class UserEntity(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con posts
    posts = db.relationship('PostEntity', backref='user', lazy=True)
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'username': self.username,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)

# DTO Class moved from UserModel
class User():
    def __init__(self, user_id, first_name, last_name, email, username, password, enabled) -> None:
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.username = username
        self.password = password
        self.enabled = enabled

    def to_json(self):
        return {        
           'user_id': self.user_id ,
           'first_name':self.first_name,
           'last_name': self.last_name,
           'email':self.email,
           'username':self.username,
           'password':self.password,
           'enabled' : self.enabled
        }  

    @classmethod
    def check_password(cls, hashed_password, password):
        return check_password_hash(hashed_password, password)
