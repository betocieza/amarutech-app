"""Add water_flat_fee to tenants

Permite pactar una tarifa plana de agua con un inquilino (ej. el 201 paga
S/ 20 fijos) en lugar del prorrateo por personas. NULL = prorrateo normal.

Revision ID: b5e2c81a9f34
Revises: a1c4e9b27f10
Create Date: 2026-09-30 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5e2c81a9f34'
down_revision = 'a1c4e9b27f10'
branch_labels = None
depends_on = None


def upgrade():
    # Nullable y sin backfill: los inquilinos existentes siguen prorrateando.
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.add_column(sa.Column('water_flat_fee', sa.Numeric(10, 2), nullable=True))


def downgrade():
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.drop_column('water_flat_fee')
