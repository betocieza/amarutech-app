#!/usr/bin/env python3
"""
Flask CLI commands for database migrations
Usage:
    python flask_commands.py db init
    python flask_commands.py db migrate -m "Add FAQ table"
    python flask_commands.py db upgrade
    python flask_commands.py set-password admin

Por defecto trabaja contra la BD local. Para la BD de Vercel (POSTGRES_URL del .env):
    $env:DB_TARGET='remote'; python flask_commands.py db upgrade; Remove-Item Env:DB_TARGET
"""

import os
import sys
import click
from flask.cli import FlaskGroup
from src import init_app
from src.database import db
from config import config

# Importar todas las entidades para que Flask-Migrate las detecte
from src.models.UserEntity import UserEntity
from src.models.PostEntity import PostEntity
from src.models.CategoryEntity import CategoryEntity
from src.models.SliderEntity import SliderEntity
from src.models.ProductEntity import ProductEntity
from src.models.FaqEntity import FaqEntity
from src.models.UnitEntity import UnitEntity
from src.models.TenantEntity import TenantEntity
from src.models.MeterEntity import MeterEntity
from src.models.UtilityBillEntity import UtilityBillEntity
from src.models.MeterReadingEntity import MeterReadingEntity
from src.models.UnitChargeEntity import UnitChargeEntity
from src.models.PaymentEntity import PaymentEntity

def create_app():
    """Create Flask app for migrations"""
    target = os.environ.get('DB_TARGET', 'development')
    if target not in config:
        raise click.ClickException(f'DB_TARGET="{target}" no válido; usa: {", ".join(config)}')
    if target == 'remote' and not config['remote'].SQLALCHEMY_DATABASE_URI:
        raise click.ClickException('Falta POSTGRES_URL en el .env')
    app = init_app(config[target])
    # Mostrar siempre contra qué BD se va a ejecutar, para no equivocarse de entorno
    url = app.config['SQLALCHEMY_DATABASE_URI']
    host = url.split('@', 1)[-1].split('?', 1)[0]
    click.secho(f'>> BD [{target}]: {host}', fg='yellow' if target == 'remote' else 'green', err=True)
    return app

cli = FlaskGroup(create_app=create_app)


@cli.command('set-password')
@click.argument('login')
def set_password(login):
    """Cambia la contraseña de un usuario (por username o email) y verifica que funcione."""
    if '@' in login:
        user = UserEntity.query.filter_by(email=login.strip().lower()).first()
    else:
        user = UserEntity.query.filter_by(username=login.strip()).first()
    if not user:
        raise click.ClickException(f'No existe el usuario "{login}"')

    password = click.prompt('Nueva contraseña', hide_input=True, confirmation_prompt='Repite la contraseña')
    if len(password) < 8:
        raise click.ClickException('La contraseña debe tener al menos 8 caracteres')

    user.set_password(password)
    db.session.commit()

    db.session.refresh(user)
    ok = user.check_password(password)
    click.echo(f'Contraseña actualizada para {user.username} <{user.email}>; verificación: {"OK" if ok else "FALLÓ"}')

if __name__ == '__main__':
    cli()