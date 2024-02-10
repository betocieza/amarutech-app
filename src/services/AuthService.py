import traceback
from werkzeug.security import check_password_hash

# Database
from src.database.db_connection_mysql import get_connection
# Logger
from src.utils.Logger import Logger
# Models
from src.models.UserModel import User


class AuthService():

    @classmethod
    def login_user(cls, user):
        try:
            connection = get_connection()           
            authenticated_user = None
 
            with connection.cursor() as cursor:
                #cursor.execute('call sp_verifyIdentity(%s, %s)', (user.username, user.password))
                #query = "SELECT id, username, password, fullname FROM users WHERE username = %s"
                query = "SELECT user_id,first_name, last_name, email, username, password, enabled FROM users WHERE username = %s"
                #print(query)
                cursor.execute(query, user.username)
                row = cursor.fetchone()
                print(row[2])               
                if row != None: 
                    if User.check_password(row[5], user.password):
                        authenticated_user = User(row[0], row[1],row[2], row[3],row[4],row[5], bool(row[6]))                      
                else:
                    return "Error em"       
            connection.close()
            return authenticated_user
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
