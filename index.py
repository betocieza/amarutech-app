from config import config

from src import init_app
from src.database import db
from flask_cors import CORS

# Importar todas las entidades para que SQLAlchemy las detecte
from src.models.UserEntity import UserEntity
from src.models.PostEntity import PostEntity  
from src.models.CategoryEntity import CategoryEntity
from src.models.SliderEntity import SliderEntity
from src.models.FaqEntity import FaqEntity

configuration = config['development']
app = init_app(configuration)
CORS(app)

# Crear las tablas en el contexto de la aplicación
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)