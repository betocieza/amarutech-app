class Post():

    def __init__(self, post_id, title, slug, description,image_url, category_id,user_id,published, created_at, updated_at) -> None:
        self.post_id = post_id
        self.title = title
        self.slug = slug
        self.description = description
        self.image_url = image_url
        self.category_id= category_id
        self.user_id = user_id       
        self.published = published
        self.created_at = created_at
        self.updated_at = updated_at

    def to_json(self):
        return {        
           'post_id': self.post_id ,
           'title':self.title,
           'slug': self.slug,
           'description':self.description,
           'image_url':self.image_url,
           'category_id':self.category_id,
           'user_id':self.user_id,
           'published': self.published,
           'created_at' : self.created_at,
           'updated_at': self.updated_at
        } 