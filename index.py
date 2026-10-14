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
from src.models.UnitEntity import UnitEntity
from src.models.TenantEntity import TenantEntity
from src.models.MeterEntity import MeterEntity
from src.models.UtilityBillEntity import UtilityBillEntity
from src.models.MeterReadingEntity import MeterReadingEntity
from src.models.UnitChargeEntity import UnitChargeEntity
from src.models.PaymentEntity import PaymentEntity

env = os.environ.get('FLASK_ENV', 'production')
configuration = config.get(env, config['production'])

app = init_app(configuration)
CORS(app)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # Flask 3 ya no deriva el modo debug de FLASK_ENV, asi que se lee
    # FLASK_DEBUG y se deja FLASK_ENV solo para elegir la configuracion.
    debug = os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true', 'on')
    app.run(debug=debug or env == 'development', port=8000)
