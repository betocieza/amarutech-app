"""Add utility billing tables (units, tenants, meters, bills, readings, charges, payments)

Revision ID: a1c4e9b27f10
Revises: 9d137158c020
Create Date: 2026-09-19 19:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1c4e9b27f10'
down_revision = '9d137158c020'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('units',
    sa.Column('unit_id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=20), nullable=False),
    sa.Column('description', sa.String(length=200), nullable=True),
    sa.Column('floor', sa.Integer(), nullable=True),
    sa.Column('is_occupied', sa.Boolean(), nullable=True),
    sa.Column('enabled', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('unit_id'),
    sa.UniqueConstraint('code')
    )

    op.create_table('tenants',
    sa.Column('tenant_id', sa.Integer(), nullable=False),
    sa.Column('unit_id', sa.Integer(), nullable=False),
    sa.Column('full_name', sa.String(length=200), nullable=False),
    sa.Column('document_number', sa.String(length=30), nullable=True),
    sa.Column('phone', sa.String(length=30), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('people_count', sa.Integer(), nullable=True),
    sa.Column('internet_fee', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('enabled', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['unit_id'], ['units.unit_id'], ),
    sa.PrimaryKeyConstraint('tenant_id')
    )

    op.create_table('meters',
    sa.Column('meter_id', sa.Integer(), nullable=False),
    sa.Column('unit_id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=30), nullable=False),
    sa.Column('valid_from', sa.Date(), nullable=False),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('enabled', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['unit_id'], ['units.unit_id'], ),
    sa.PrimaryKeyConstraint('meter_id')
    )

    op.create_table('utility_bills',
    sa.Column('bill_id', sa.Integer(), nullable=False),
    sa.Column('service_type', sa.String(length=20), nullable=False),
    sa.Column('period', sa.String(length=7), nullable=False),
    sa.Column('period_start', sa.Date(), nullable=True),
    sa.Column('period_end', sa.Date(), nullable=True),
    sa.Column('total_amount', sa.Numeric(precision=12, scale=4), nullable=False),
    sa.Column('total_units', sa.Numeric(precision=12, scale=4), nullable=False),
    sa.Column('unit_price', sa.Numeric(precision=12, scale=8), nullable=False),
    sa.Column('due_date', sa.Date(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('bill_id'),
    sa.UniqueConstraint('service_type', 'period', name='uq_utility_bill_service_period')
    )

    op.create_table('meter_readings',
    sa.Column('reading_id', sa.Integer(), nullable=False),
    sa.Column('meter_id', sa.Integer(), nullable=False),
    sa.Column('period', sa.String(length=7), nullable=False),
    sa.Column('previous_date', sa.Date(), nullable=True),
    sa.Column('current_date', sa.Date(), nullable=True),
    sa.Column('previous_reading', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('current_reading', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('consumption', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['meter_id'], ['meters.meter_id'], ),
    sa.PrimaryKeyConstraint('reading_id'),
    sa.UniqueConstraint('meter_id', 'period', name='uq_meter_reading_meter_period')
    )

    op.create_table('unit_charges',
    sa.Column('charge_id', sa.Integer(), nullable=False),
    sa.Column('unit_id', sa.Integer(), nullable=False),
    sa.Column('tenant_id', sa.Integer(), nullable=True),
    sa.Column('period', sa.String(length=7), nullable=False),
    sa.Column('period_start', sa.Date(), nullable=True),
    sa.Column('period_end', sa.Date(), nullable=True),
    sa.Column('electricity_consumption', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('electricity_price', sa.Numeric(precision=12, scale=8), nullable=True),
    sa.Column('electricity_amount', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('water_people', sa.Integer(), nullable=True),
    sa.Column('water_price', sa.Numeric(precision=12, scale=8), nullable=True),
    sa.Column('water_amount', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('internet_amount', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('previous_credit', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('total_amount', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('paid_amount', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('credit_balance', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id'], ),
    sa.ForeignKeyConstraint(['unit_id'], ['units.unit_id'], ),
    sa.PrimaryKeyConstraint('charge_id'),
    sa.UniqueConstraint('unit_id', 'period', name='uq_unit_charge_unit_period')
    )

    op.create_table('payments',
    sa.Column('payment_id', sa.Integer(), nullable=False),
    sa.Column('charge_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=12, scale=4), nullable=False),
    sa.Column('payment_date', sa.Date(), nullable=False),
    sa.Column('method', sa.String(length=50), nullable=True),
    sa.Column('reference', sa.String(length=100), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['charge_id'], ['unit_charges.charge_id'], ),
    sa.PrimaryKeyConstraint('payment_id')
    )


def downgrade():
    op.drop_table('payments')
    op.drop_table('unit_charges')
    op.drop_table('meter_readings')
    op.drop_table('utility_bills')
    op.drop_table('meters')
    op.drop_table('tenants')
    op.drop_table('units')
