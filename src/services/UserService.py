import traceback
# SQLAlchemy
from src.models.UserEntity import UserEntity
from src.database import db
# Logger
from src.utils.Logger import Logger
# Models
from src.models.UserEntity import User


class UserService():

# Methods for admin  
    @classmethod
    def get_users(cls):
        try:
            users = []
            # Obtener todos los usuarios
            user_entities = UserEntity.query.all()
            
            for user_entity in user_entities:
                user = User(
                    user_id=user_entity.user_id,
                    first_name=user_entity.first_name,
                    last_name=user_entity.last_name,
                    email=user_entity.email,
                    username=user_entity.username,
                    password=user_entity.password,
                    enabled=user_entity.enabled
                )
                users.append(user.to_json())
            return users
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return []

    @classmethod
    def getUserById(cls, user_id):
        try:
            user_entity = UserEntity.query.get(user_id)
            if user_entity:
                return user_entity.to_dict()
            return None
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None
    
    @classmethod
    def getUserByUsername(cls, username):
        try:
            user_entity = UserEntity.query.filter_by(username=username).first()
            if user_entity:
                return user_entity
            return None
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None
    
    # Method for insert new User
    @classmethod
    def saveUser(cls, user):
        try:
            new_user = UserEntity(
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                username=user.username,
                enabled=user.enabled
            )
            new_user.set_password(user.password)  # Hash the password
            db.session.add(new_user)
            db.session.commit()
            return "User add success"
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return "Error adding user"

    # Method for update User
    @classmethod
    def updateUser(cls, user_id, user):
        try:
            user_entity = UserEntity.query.get(user_id)
            if user_entity:
                user_entity.first_name = user.first_name
                user_entity.last_name = user.last_name
                user_entity.email = user.email
                user_entity.username = user.username
                user_entity.enabled = user.enabled
                
                if hasattr(user, 'password') and user.password:
                    user_entity.set_password(user.password)
                
                db.session.commit()
                return "User updated successfully"
            return "User not found"
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return "Error updating user"
