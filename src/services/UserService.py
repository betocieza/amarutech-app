import traceback
# Database
from src.database.db_connection import get_connection
# Logger
from src.utils.Logger import Logger
# Models
from src.models.UserModel import User


class UserService():


# Methods for admin  
    @classmethod
    def get_users(cls):
        try:
            connection = get_connection()
            users = []
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users")
                resultset = cursor.fetchall()
                for row in resultset:
                    user = User(int(row[0]), row[1],row[2],row[3],row[4],row[5],row[6])
                    users.append(user.to_json())
            connection.close()
            return users
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())



    @classmethod
    def getuserById(cls,user_id):
        try:
            connection = get_connection()   
           # user = []        
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE user_id = '{0}'".format(user_id))
                data = cursor.fetchone()              
                if data!=None:
                    user = {'user_id':data[0],'title':data[1],'slug':data[2],'description':data[3],'image_url':data[4],'category_id':data[5],'user_id':data[6],'published':data[7],'created_at':data[8],'updated_at':data[9]} 
                                      
            connection.close()
            return user
        
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
    
    # Method for insert new user
    @classmethod
    def saveUser(cls, user):
        try:
            connection = get_connection()                   
            with connection.cursor() as cursor:
                query = """INSERT INTO users (title, subtitle, link,image_url,published, created_at, updated_at) 
                VALUES ('{0}', '{1}', '{2}' ,'{3}', '{4}' ,'{5}', '{6}')""".format(user.title, user.subtitle, user.link,user.image_url, user.published,user.created_at, user.updated_at)
                cursor.execute(query)
                connection.commit()                                    
            connection.close()
            return "user add sucess"
        
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())

    # Method for update user
    @classmethod
    def updateUser(cls, user_id, user):
        try:       
            connection = get_connection()            
            with connection.cursor() as cursor:
                query = """UPDATE users SET title = '{0}',subtitle = '{1}',link = '{2}',image_url='{3}', published='{4}',updated_at='{5}'
                            WHERE user_id= '{6}'""".format(user.title, user.subtitle,user.link,user.image_url,user.published,user.updated_at, user_id)
                
                cursor.execute(query)
                connection.commit()                                    
            connection.close()
            return "user updated sucess"
        
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
