from flask import Flask


# Routes
from .controllers import AuthController,IndexController,PostController,CategoryController,SliderController,UserController
app = Flask(__name__)


def init_app(config):
    # Configuration
    app.config.from_object(config)
  
    # Blueprints
    app.register_blueprint(IndexController.main, url_prefix='/')
    app.register_blueprint(AuthController.main, url_prefix='/api/auth') 
    app.register_blueprint(UserController.main, url_prefix='/api/users') 
    app.register_blueprint(PostController.main, url_prefix='/api/posts') 
    app.register_blueprint(CategoryController.main, url_prefix='/api/categories') 
    app.register_blueprint(SliderController.main, url_prefix='/api/sliders') 
  

    return app