import traceback
# Database
from src.database.db_connection import get_connection
# Logger
from src.utils.Logger import Logger
# Models
from src.models.PostModel import Post


class PostService():
# Methods for front web
 
    @classmethod
    def get_list_posts(cls):
        try:
            connection = get_connection()
            posts = []
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM posts ORDER BY created_at DESC LIMIT 4")
                resultset = cursor.fetchall()
                for row in resultset:
                    post = Post(int(row[0]), row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8])
                    posts.append(post.to_json())
            connection.close()
            return posts
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())

# Methods for admin  
    @classmethod
    def get_posts(cls):
        try:
            connection = get_connection()
            posts = []
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM posts ORDER BY created_at")
                resultset = cursor.fetchall()
                for row in resultset:
                    post = Post(int(row[0]), row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8])
                    posts.append(post.to_json())
            connection.close()
            return posts
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
                    post = {'post_id':data[0],'title':data[1],'slug':data[2],'description':data[3],'image_url':data[4],'user_id':data[5],'published':data[6],'created_at':data[7],'updated_at':data[8]} 
                                      
            connection.close()
            return post
        
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
    
    # Method for insert new Post
    @classmethod
    def savePost(cls, post):
        try:
            connection = get_connection()                   
            with connection.cursor() as cursor:
                query = """INSERT INTO posts (title, slug, description,image_url,user_id,published, created_at, updated_at) 
                VALUES ('{0}', '{1}', '{2}' ,'{3}', '{4}' ,'{5}', '{6}','{7}')""".format(post.title, post.slug, post.description,post.image_url, post.user_id, post.published,post.created_at, post.updated_at)
                print(query)
                cursor.execute(query)
                connection.commit()                                    
            connection.close()
            return "Post add sucess"
        
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())

    # Method for update Post
    @classmethod
    def updatePost(cls, post_id, post):
        try:       
            connection = get_connection()            
            with connection.cursor() as cursor:
                query = """UPDATE posts SET title = '{0}',slug = '{1}',description = '{2}',image_url='{3}', user_id='{4}', published='{5}',updated_at='{6}'
                            WHERE post_id= '{7}'""".format(post.title, post.slug,post.description,post.image_url,post.user_id,post.published,post.updated_at, post_id)
                
                cursor.execute(query)
                connection.commit()                                    
            connection.close()
            return "Post updated sucess"
        
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
