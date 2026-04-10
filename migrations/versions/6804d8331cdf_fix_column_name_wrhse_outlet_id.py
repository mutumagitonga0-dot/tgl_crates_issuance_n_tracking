"""Fix column name wrhse_outlet_id

Revision ID: 6804d8331cdf
Revises: 098247665e48
Create Date: 2026-04-10 14:23:46.244158

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6804d8331cdf'
down_revision = '098247665e48'
branch_labels = None
depends_on = None


def upgrade():
    # warehouse_transactions: rename Wrhse_outlet_id -> wrhse_outlet_id
    with op.batch_alter_table('warehouse_transactions', schema=None) as batch_op:
        batch_op.alter_column('Wrhse_outlet_id', new_column_name='wrhse_outlet_id')

    # warehouses: rename Whrsh_Outlets_id -> whrsh_outlets_id
    with op.batch_alter_table('warehouses', schema=None) as batch_op:
        batch_op.alter_column('Whrsh_Outlets_id', new_column_name='whrsh_outlets_id')


def downgrade():
    # revert the renames
    with op.batch_alter_table('warehouses', schema=None) as batch_op:
        batch_op.alter_column('whrsh_outlets_id', new_column_name='Whrsh_Outlets_id')

    with op.batch_alter_table('warehouse_transactions', schema=None) as batch_op:
        batch_op.alter_column('wrhse_outlet_id', new_column_name='Wrhse_outlet_id')

