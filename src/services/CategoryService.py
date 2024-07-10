import traceback
# Database
from src.database.db_connection import get_connection
# Logger
from src.utils.Logger import Logger
# Models
from src.models.CategoryModel import Category


class CategoryService():

# Methods for admin  
    @classmethod
    def get_categories(cls):
        try:
            connection = get_connection()
            categories = []
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM categories ORDER BY created_at")
                resultset = cursor.fetchall()
                for row in resultset:
                    category = Category(int(row[0]), row[1],row[2],row[3])
                    categories.append(category.to_json())
            connection.close()
            return categories
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())



    @classmethod
    def getPostById(cls,post_id):
        try:
            connection = get_connection()   
           # Post = []        
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM posts WHERE post_id = '{0}'".format(post_id))
                data = cursor.fetchone()              
                if data!=None:
                    post = {'post_id':data[0],'title':data[1],'slug':data[2],'description':data[3],'image_url':data[4],'category_id':data[5],'user_id':data[6],'published':data[7],'created_at':data[8],'updated_at':data[9]} 
                                      
            connection.close()
            return post
        
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
    
    # Method for insert new Post
    @classmethod
    def saveCategory(cls, category):
        try:
            connection = get_connection()                   
            with connection.cursor() as cursor:
                query = """INSERT INTO categories (name, created_at, updated_at) 
                VALUES ('{0}', '{1}', '{2}' )""".format(category.name, category.created_at, category.updated_at)
                cursor.execute(query)
                connection.commit()                                    
            connection.close()
            return "Category add sucess"
        
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())

    # Method for update Post
    @classmethod
    def updateCategory(cls, category_id, category):
        try:       
            connection = get_connection()            
            with connection.cursor() as cursor:
                query = """UPDATE categories SET name = '{0}',updated_at='{1}'
                            WHERE category_id= '{2}'""".format(category.name, category.updated_at, category_id)
                
                cursor.execute(query)
                connection.commit()                                    
            connection.close()
            return "Post updated sucess"
        
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
