from decouple import config


def normalize_db_url(url):
    """Vercel/Neon entregan postgres://; SQLAlchemy necesita el driver explícito (psycopg 3)."""
    for prefix in ('postgres://', 'postgresql://'):
        if url.startswith(prefix):
            return 'postgresql+psycopg://' + url[len(prefix):]
    return url


class Config():
    SECRET_KEY = config('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg://{config('POSTGRES_USER')}:{config('POSTGRES_PASSWORD')}@{config('POSTGRES_HOST')}/{config('POSTGRES_DATABASE')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class RemoteConfig(ProductionConfig):
    """BD de Vercel (POSTGRES_URL). Solo se usa a pedido, p. ej. para correr migraciones en producción."""
    SQLALCHEMY_DATABASE_URI = normalize_db_url(config('POSTGRES_URL', default=''))
    # El pooler de Neon (pgbouncer en modo transacción) no admite sentencias preparadas
    SQLALCHEMY_ENGINE_OPTIONS = {'connect_args': {'prepare_threshold': None}}


config = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'remote':      RemoteConfig
}
