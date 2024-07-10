class Slider():

    def __init__(self, slider_id, title, subtitle, link,image_url,published, created_at, updated_at) -> None:
        self.slider_id = slider_id
        self.title = title
        self.subtitle = subtitle
        self.link = link
        self.image_url = image_url
        self.published = published
        self.created_at = created_at
        self.updated_at = updated_at

    def to_json(self):
        return {        
           'slider_id': self.slider_id ,
           'title':self.title,
           'subtitle': self.subtitle,
           'link':self.link,
           'image_url':self.image_url,
           'published': self.published,
           'created_at' : self.created_at,
           'updated_at': self.updated_at
        } 