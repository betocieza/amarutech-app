class Category():

    def __init__(self, category_id, name,created_at, updated_at) -> None:
        self.category_id = category_id
        self.name = name
        self.created_at = created_at
        self.updated_at = updated_at

    def to_json(self):
        return {        
           'category_id': self.category_id ,
           'name':self.name,
           'created_at' : self.created_at,
           'updated_at': self.updated_at
        } 