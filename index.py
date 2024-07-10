from config import config
#from decouple import config
#import b2sdk.v2 as b2
from src import init_app
from flask_cors import CORS
#info = b2.InMemoryAccountInfo()
#b2_api = b2.B2Api(info)


#application_key_id = config("B2_KEY_ID")
#application_key = config("B2_APP_KEY")

#b2_api.authorize_account("production", application_key_id, application_key)
#bucket = b2_api.get_bucket_by_name("amarutech-files")

configuration = config['development']
app = init_app(configuration)
CORS(app)
#CORS(app,origins=["http://localhost:4200"])



if __name__ == '__main__':
    app.run(debug=True)