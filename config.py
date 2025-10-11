from decouple import config


class Config():
    SECRET_KEY = config('SECRET_KEY')
    # Configuración de SQLAlchemy usando psycopg (no psycopg2)
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg://{config('POSTGRES_USER')}:{config('POSTGRES_PASSWORD')}@{config('POSTGRES_HOST')}/{config('POSTGRES_DATABASE')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True


config = {
    'development': DevelopmentConfig
}