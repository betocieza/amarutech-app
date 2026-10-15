"""Add products table

Los productos de la web pública vivían en una constante del front
(product-data.const.ts). Se pasan a una tabla para gestionarlos desde el
admin, con imagen subida a Backblaze. Se siembran los productos existentes.

Revision ID: d4a8b1e63c72
Revises: c7f3a2d91e05
Create Date: 2026-10-15 10:00:00.000000

"""
from datetime import datetime
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4a8b1e63c72'
down_revision = 'c7f3a2d91e05'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    # index.py hace db.create_all() al arrancar: si la app corrió antes que esta
    # migración, la tabla ya existe (vacía) y solo falta sembrarla.
    if not sa.inspect(bind).has_table('products'):
        create_products_table()

    if bind.execute(sa.text('SELECT COUNT(*) FROM products')).scalar() == 0:
        seed_products()


def create_products_table():
    op.create_table(
        'products',
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('tagline', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('tags', sa.String(length=500), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('link', sa.String(length=500), nullable=True),
        sa.Column('published', sa.Boolean(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('product_id'),
        sa.UniqueConstraint('slug')
    )


def seed_products():
    products = sa.table(
        'products',
        sa.column('slug', sa.String), sa.column('name', sa.String), sa.column('tagline', sa.String),
        sa.column('description', sa.Text), sa.column('icon', sa.String), sa.column('tags', sa.String),
        sa.column('image_url', sa.String), sa.column('link', sa.String), sa.column('published', sa.Boolean),
        sa.column('sort_order', sa.Integer), sa.column('created_at', sa.DateTime), sa.column('updated_at', sa.DateTime)
    )
    now = datetime.utcnow()
    op.bulk_insert(products, [
        {
            'slug': 'nexfarma',
            'name': 'NexFarma',
            'tagline': 'Sistema de gestión de farmacias',
            'description': 'Plataforma integral para la administración de farmacias: control de inventario, ventas, vencimientos y reportes en tiempo real, pensada para optimizar la operación diaria del negocio.',
            'icon': 'pill',
            'tags': '["SaaS", "Inventario", "Punto de venta"]',
            'image_url': None,
            'link': 'https://www.nexfarma.app/',
            'published': True,
            'sort_order': 1,
            'created_at': now,
            'updated_at': now
        },
        {
            'slug': 'eyediagnose',
            'name': 'Eyediagnose',
            'tagline': 'Detección de retinopatía diabética con IA',
            'description': 'Sistema de apoyo al diagnóstico que utiliza inteligencia artificial para la detección temprana de retinopatía diabética a partir de imágenes de fondo de ojo, agilizando la revisión clínica.',
            'icon': 'eye',
            'tags': '["IA", "Visión", "Salud"]',
            'image_url': None,
            'link': None,
            'published': True,
            'sort_order': 2,
            'created_at': now,
            'updated_at': now
        }
    ])


def downgrade():
    op.drop_table('products')
