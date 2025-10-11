from flask import Flask
from src.database import db
from flask_migrate import Migrate

# Routes
from .controllers import AuthController,IndexController,PostController,CategoryController,SliderController,UserController,FaqController
app = Flask(__name__)
migrate = Migrate()

def init_app(config):
    # Configuration
    app.config.from_object(config)
    
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Initialize Flask-Migrate
    migrate.init_app(app, db)
  
    # Blueprints
    app.register_blueprint(IndexController.main, url_prefix='/')
    app.register_blueprint(AuthController.main, url_prefix='/api/auth') 
    app.register_blueprint(UserController.main, url_prefix='/api/users') 
    app.register_blueprint(PostController.main, url_prefix='/api/posts') 
    app.register_blueprint(CategoryController.main, url_prefix='/api/categories') 
    app.register_blueprint(SliderController.main, url_prefix='/api/sliders') 
    app.register_blueprint(FaqController.main, url_prefix='/api/faqs') 
  

    return app