import traceback
# SQLAlchemy
from src.models.UserEntity import UserEntity
from src.database import db
# Logger
from src.utils.Logger import Logger


class UserService():
    """Operaciones sobre usuarios del panel.

    Los métodos de escritura devuelven (ok, mensaje) para que el controlador
    distinga el éxito del error; nunca exponen el hash de la contraseña.
    """

# Methods for admin
    @classmethod
    def get_users(cls):
        try:
            user_entities = UserEntity.query.order_by(UserEntity.user_id).all()
            return [user_entity.to_dict() for user_entity in user_entities]
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return []

    @classmethod
    def getUserById(cls, user_id):
        try:
            user_entity = db.session.get(UserEntity, user_id)
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

    @classmethod
    def _duplicate_message(cls, username, email, exclude_id=None):
        """Mensaje si el usuario o el email ya están en uso por otra cuenta."""
        query = UserEntity.query
        if exclude_id is not None:
            query = query.filter(UserEntity.user_id != exclude_id)
        if username and query.filter(UserEntity.username == username).first():
            return "El nombre de usuario ya está en uso"
        if email and query.filter(UserEntity.email == email).first():
            return "El email ya está registrado"
        return None

    # Method for insert new User
    @classmethod
    def saveUser(cls, user):
        try:
            duplicate = cls._duplicate_message(user.username, user.email)
            if duplicate:
                return False, duplicate, None

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
            return True, "Usuario creado correctamente", new_user.to_dict()
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return False, "Error al crear el usuario", None

    # Method for update User
    @classmethod
    def updateUser(cls, user_id, user):
        try:
            user_entity = db.session.get(UserEntity, user_id)
            if not user_entity:
                return False, "Usuario no encontrado"

            duplicate = cls._duplicate_message(user.username, user.email, exclude_id=user_entity.user_id)
            if duplicate:
                return False, duplicate

            user_entity.first_name = user.first_name
            user_entity.last_name = user.last_name
            user_entity.email = user.email
            user_entity.username = user.username
            user_entity.enabled = user.enabled

            # La contraseña solo cambia si se envía una nueva
            if user.password:
                user_entity.set_password(user.password)

            db.session.commit()
            return True, "Usuario actualizado correctamente"
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return False, "Error al actualizar el usuario"

    # Method for delete User
    @classmethod
    def deleteUser(cls, user_id):
        try:
            user_entity = db.session.get(UserEntity, user_id)
            if not user_entity:
                return False, "Usuario no encontrado"
            if user_entity.posts:
                return False, "No se puede eliminar: el usuario tiene posts. Desactívalo en su lugar."

            db.session.delete(user_entity)
            db.session.commit()
            return True, "Usuario eliminado correctamente"
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return False, "Error al eliminar el usuario"
