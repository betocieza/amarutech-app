import traceback
# SQLAlchemy
from src.models.SliderEntity import SliderEntity
from src.database import db
# Logger
from src.utils.Logger import Logger
# Models
from src.models.SliderEntity import Slider


class SliderService():
# Methods for front web
 
    @classmethod
    def get_list_sliders(cls):
        try:
            sliders = []
            # Obtener sliders publicados ordenados por sort_order y fecha
            slider_entities = SliderEntity.query.filter_by(
                published=True
            ).order_by(SliderEntity.sort_order.asc(), SliderEntity.created_at.desc()).limit(4).all()
            
            for slider_entity in slider_entities:
                slider = Slider(
                    slider_id=slider_entity.slider_id,
                    title=slider_entity.title,
                    subtitle=slider_entity.subtitle,
                    link=slider_entity.link,
                    image_url=slider_entity.image_url,
                    published=slider_entity.published,
                    sort_order=slider_entity.sort_order,
                    created_at=slider_entity.created_at,
                    updated_at=slider_entity.updated_at
                )
                sliders.append(slider.to_json())
            return sliders
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return []

# Methods for admin  
    @classmethod
    def get_sliders(cls):
        try:
            sliders = []
            # Obtener todos los sliders ordenados por sort_order y fecha de creación
            slider_entities = SliderEntity.query.order_by(SliderEntity.sort_order.asc(), SliderEntity.created_at.desc()).all()
            
            for slider_entity in slider_entities:
                slider = Slider(
                    slider_id=slider_entity.slider_id,
                    title=slider_entity.title,
                    subtitle=slider_entity.subtitle,
                    link=slider_entity.link,
                    image_url=slider_entity.image_url,
                    published=slider_entity.published,
                    sort_order=slider_entity.sort_order,
                    created_at=slider_entity.created_at,
                    updated_at=slider_entity.updated_at
                )
                sliders.append(slider.to_json())
            return sliders
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return []

    @classmethod
    def getSliderById(cls, slider_id):
        try:
            slider_entity = SliderEntity.query.get(slider_id)
            if slider_entity:
                return slider_entity.to_dict()
            return None
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None
    
    # Method for insert new Slider
    @classmethod
    def saveSlider(cls, slider):
        try:
            new_slider = SliderEntity(
                title=slider.title,
                subtitle=slider.subtitle,
                link=slider.link,
                image_url=slider.image_url,
                published=slider.published,
                sort_order=getattr(slider, 'sort_order', 0)
            )
            db.session.add(new_slider)
            db.session.commit()
            return "Slider add success"
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return "Error adding slider"

    # Method for update Slider
    @classmethod
    def updateSlider(cls, slider_id, slider):
        try:
            slider_entity = SliderEntity.query.get(slider_id)
            if slider_entity:
                slider_entity.title = slider.title
                slider_entity.subtitle = slider.subtitle
                slider_entity.link = slider.link
                slider_entity.image_url = slider.image_url
                slider_entity.published = slider.published
                slider_entity.sort_order = getattr(slider, 'sort_order', slider_entity.sort_order)
                
                db.session.commit()
                return "Slider updated successfully"
            return "Slider not found"
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return "Error updating slider"
