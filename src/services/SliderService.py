import traceback
# Database
from src.database.db_connection import get_connection
# Logger
from src.utils.Logger import Logger
# Models
from src.models.SliderModel import Slider


class SliderService():
# Methods for front web
 
    @classmethod
    def get_list_sliders(cls):
        try:
            connection = get_connection()
            sliders = []
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM sliders WHERE published= true AND category_id=1 ORDER BY created_at DESC LIMIT 4")
                resultset = cursor.fetchall()
                for row in resultset:
                    slider = slider(int(row[0]), row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9])
                    sliders.append(slider.to_json())
            connection.close()
            return sliders
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())




# Methods for admin  
    @classmethod
    def get_sliders(cls):
        try:
            connection = get_connection()
            sliders = []
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM sliders ORDER BY created_at")
                resultset = cursor.fetchall()
                for row in resultset:
                    slider = Slider(int(row[0]), row[1],row[2],row[3],row[4],row[5],row[6],row[7])
                    sliders.append(slider.to_json())
            connection.close()
            return sliders
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())



    @classmethod
    def getSliderById(cls,slider_id):
        try:
            connection = get_connection()   
           # slider = []        
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM sliders WHERE slider_id = '{0}'".format(slider_id))
                data = cursor.fetchone()              
                if data!=None:
                    slider = {'slider_id':data[0],'title':data[1],'slug':data[2],'description':data[3],'image_url':data[4],'category_id':data[5],'user_id':data[6],'published':data[7],'created_at':data[8],'updated_at':data[9]} 
                                      
            connection.close()
            return slider
        
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
    
    # Method for insert new slider
    @classmethod
    def saveSlider(cls, slider):
        try:
            connection = get_connection()                   
            with connection.cursor() as cursor:
                query = """INSERT INTO sliders (title, subtitle, link,image_url,published, created_at, updated_at) 
                VALUES ('{0}', '{1}', '{2}' ,'{3}', '{4}' ,'{5}', '{6}')""".format(slider.title, slider.subtitle, slider.link,slider.image_url, slider.published,slider.created_at, slider.updated_at)
                cursor.execute(query)
                connection.commit()                                    
            connection.close()
            return "Slider add sucess"
        
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())

    # Method for update slider
    @classmethod
    def updateSlider(cls, slider_id, slider):
        try:       
            connection = get_connection()            
            with connection.cursor() as cursor:
                query = """UPDATE sliders SET title = '{0}',subtitle = '{1}',link = '{2}',image_url='{3}', published='{4}',updated_at='{5}'
                            WHERE slider_id= '{6}'""".format(slider.title, slider.subtitle,slider.link,slider.image_url,slider.published,slider.updated_at, slider_id)
                
                cursor.execute(query)
                connection.commit()                                    
            connection.close()
            return "slider updated sucess"
        
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
