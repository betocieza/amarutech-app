#!/usr/bin/env python3
"""
Flask CLI commands for database migrations
Usage:
    python flask_commands.py db init
    python flask_commands.py db migrate -m "Add FAQ table"
    python flask_commands.py db upgrade
"""

import os
import sys
from flask.cli import FlaskGroup
from src import init_app
from config import config

# Importar todas las entidades para que Flask-Migrate las detecte
from src.models.UserEntity import UserEntity
from src.models.PostEntity import PostEntity
from src.models.CategoryEntity import CategoryEntity
from src.models.SliderEntity import SliderEntity
from src.models.FaqEntity import FaqEntity

def create_app():
    """Create Flask app for migrations"""
    app = init_app(config['development'])
    return app

cli = FlaskGroup(create_app=create_app)

if __name__ == '__main__':
    cli()