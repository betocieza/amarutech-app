import traceback
from werkzeug.security import check_password_hash

# SQLAlchemy
from src.models.UserEntity import UserEntity
# Logger
from src.utils.Logger import Logger
# Models
from src.models.UserEntity import User


class AuthService():

    @classmethod
    def login_user(cls, user):
        try:
            authenticated_user = None
            
            # Buscar usuario por username usando SQLAlchemy
            user_entity = UserEntity.query.filter_by(username=user.username).first()
            
            if user_entity and user_entity.enabled:
                # Verificar password usando el método del modelo ORM
                if user_entity.check_password(user.password):
                    authenticated_user = User(
                        user_id=user_entity.user_id,
                        first_name=user_entity.first_name,
                        last_name=user_entity.last_name,
                        email=user_entity.email,
                        username=user_entity.username,
                        password=user_entity.password,
                        enabled=user_entity.enabled
                    )
            
            return authenticated_user
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None
