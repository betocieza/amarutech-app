"""Add execution_year to posts

Revision ID: c7f3a2d91e05
Revises: b5e2c81a9f34
Create Date: 2026-10-14 23:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7f3a2d91e05'
down_revision = 'b5e2c81a9f34'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('posts', sa.Column('execution_year', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('posts', 'execution_year')
