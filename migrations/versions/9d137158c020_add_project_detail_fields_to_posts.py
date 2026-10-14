"""Add project detail fields to posts table

Revision ID: 9d137158c020
Revises: 671ff6f15bc4
Create Date: 2026-07-18 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d137158c020'
down_revision = '671ff6f15bc4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('posts', sa.Column('executing_company', sa.String(length=255), nullable=True))
    op.add_column('posts', sa.Column('associated_partner', sa.String(length=255), nullable=True))
    op.add_column('posts', sa.Column('competitive_fund', sa.String(length=255), nullable=True))
    op.add_column('posts', sa.Column('investment_amount', sa.String(length=100), nullable=True))


def downgrade():
    op.drop_column('posts', 'investment_amount')
    op.drop_column('posts', 'competitive_fund')
    op.drop_column('posts', 'associated_partner')
    op.drop_column('posts', 'executing_company')
