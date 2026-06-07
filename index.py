import os
from config import config

from src import init_app
from src.database import db
from flask_cors import CORS

from src.models.UserEntity import UserEntity
from src.models.PostEntity import PostEntity
from src.models.CategoryEntity import CategoryEntity
from src.models.SliderEntity import SliderEntity
from src.models.FaqEntity import FaqEntity

env = os.environ.get('FLASK_ENV', 'production')
configuration = config.get(env, config['production'])

app = init_app(configuration)
CORS(app)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=(env == 'development'))
