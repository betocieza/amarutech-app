from werkzeug.security import check_password_hash, generate_password_hash

class User():

    def __init__(self, user_id, first_name, last_name, email,username, password, enabled) -> None:
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.username = username
        self.password = password
        self.enabled = enabled

    def to_json(self):
        return {        
           'user_id': self.user_id ,
           'first_name':self.first_name,
           'last_name': self.last_name,
           'email':self.email,
           'username':self.username,
           'password':self.password,
           'enabled' : self.enabled
        }  

    @classmethod
    def check_password(self, hashed_password, password):
        return check_password_hash(hashed_password, password)
#print("pass:",generate_password_hash("1234"))

   