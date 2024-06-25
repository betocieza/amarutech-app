from flask import Flask


# Routes
from .controllers import AuthController,IndexController,PostController
app = Flask(__name__)


def init_app(config):
    # Configuration
    app.config.from_object(config)
  
    # Blueprints
    app.register_blueprint(IndexController.main, url_prefix='/')
    app.register_blueprint(AuthController.main, url_prefix='/api/auth') 
    #app.register_blueprint(UserRoutes.main, url_prefix='/users') 
    app.register_blueprint(PostController.main, url_prefix='/api/posts') 
  

    return app