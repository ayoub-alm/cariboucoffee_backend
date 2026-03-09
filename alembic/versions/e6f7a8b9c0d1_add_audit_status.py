"""Add status column to audits table

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-03-06 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'e6f7a8b9c0d1'
down_revision = 'd5e6f7a8b9c0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('audits', sa.Column('status', sa.String(), server_default='COMPLETED', nullable=True))
    op.execute("UPDATE audits SET status = 'COMPLETED' WHERE status IS NULL")


def downgrade() -> None:
    op.drop_column('audits', 'status')
