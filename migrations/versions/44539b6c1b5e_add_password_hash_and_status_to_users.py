"""Add password_hash and status to Users

Revision ID: 44539b6c1b5e
Revises: 
Create Date: 2026-05-01 17:57:28.106506

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '44539b6c1b5e'
down_revision = None
branch_labels = None
depends_on = None


def downgrade():
    op.drop_column('users', 'password_hash')
    op.drop_column('users', 'status')

def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    columns = [col['name'] for col in inspector.get_columns('users')]

    if 'password_hash' not in columns:
        op.add_column('users', sa.Column('password_hash', sa.String(length=200), nullable=False))

    if 'status' not in columns:
        op.add_column('users', sa.Column('status', sa.Integer(), nullable=False))

