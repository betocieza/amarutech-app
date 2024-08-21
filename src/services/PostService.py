import traceback
# Database
from src.database.db_connection import get_connection
# Logger
from src.utils.Logger import Logger
# Models
from src.models.PostModel import Post, PostCategory, PostMonth


class PostService():
# Methods for front web
 
    @classmethod
    def get_list_posts(cls):
        try:
            connection = get_connection()
            posts = []
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM posts WHERE published= true AND category_id=1 ORDER BY created_at DESC LIMIT 4")
                resultset = cursor.fetchall()
                for row in resultset:
                    post = Post(int(row[0]), row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9])
                    posts.append(post.to_json())
            connection.close()
            return posts
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())


    @classmethod
    def get_list_news(cls):
        try:
            connection = get_connection()
            posts = []
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM posts WHERE published= true AND category_id=2 ORDER BY created_at DESC LIMIT 4")
                resultset = cursor.fetchall()
                for row in resultset:
                    post = Post(int(row[0]), row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9])
                    posts.append(post.to_json())
            connection.close()
            return posts
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())

# Methods for admin  
    @classmethod
    def get_posts_by_month(cls):
        try:
            connection = get_connection()
            posts = []
            with connection.cursor() as cursor:
                cursor.execute("SELECT to_char(created_at,'MON') AS monthName,COUNT(*) AS numberPosts FROM posts GROUP BY to_char(created_at,'MON') ORDER BY to_char(created_at,'MON') ASC")
                resultset = cursor.fetchall()
                for row in resultset:
                    post = PostMonth(row[0], row[1])
                    posts.append(post.to_json())
            connection.close()
            return posts
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())

    @classmethod
    def get_posts_by_category(cls):
        try:
            connection = get_connection()
            posts = []
            with connection.cursor() as cursor:
                cursor.execute("SELECT category_id as category, count(*) as numberPost from posts group by category_id")
                resultset = cursor.fetchall()
                for row in resultset:
                    post = PostCategory(row[0], row[1])
                    posts.append(post.to_json())
            connection.close()
            return posts
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())

    @classmethod
    def get_posts(cls):
        try:
            connection = get_connection()
            posts = []
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM posts ORDER BY created_at")
                resultset = cursor.fetchall()
                for row in resultset:
                    post = Post(int(row[0]), row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9])
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
                    post = {'post_id':data[0],'title':data[1],'slug':data[2],'description':data[3],'image_url':data[4],'category_id':data[5],'user_id':data[6],'published':data[7],'created_at':data[8],'updated_at':data[9]} 
                                      
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
                query = """INSERT INTO posts (title, slug, description,image_url,category_id,user_id,published, created_at, updated_at) 
                VALUES ('{0}', '{1}', '{2}' ,'{3}', '{4}' ,'{5}', '{6}','{7}','{8}')""".format(post.title, post.slug, post.description,post.image_url, post.category_id, post.user_id, post.published,post.created_at, post.updated_at)
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
                query = """UPDATE posts SET title = '{0}',slug = '{1}',description = '{2}',image_url='{3}', category_id='{4}',user_id='{5}', published='{6}',updated_at='{7}'
                            WHERE post_id= '{8}'""".format(post.title, post.slug,post.description,post.image_url,post.category_id,post.user_id,post.published,post.updated_at, post_id)
                
                cursor.execute(query)
                connection.commit()                                    
            connection.close()
            return "Post updated sucess"
        
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
