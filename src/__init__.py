from flask import Flask


# Routes
from .controllers import AuthController,IndexController
app = Flask(__name__)


def init_app(config):
    # Configuration
    app.config.from_object(config)
  
    # Blueprints
    app.register_blueprint(IndexController.main, url_prefix='/')
    app.register_blueprint(AuthController.main, url_prefix='/auth') 
    #app.register_blueprint(UserRoutes.main, url_prefix='/users') 
    #sapp.register_blueprint(PostRoutes.main, url_prefix='/posts') 
  

    return app