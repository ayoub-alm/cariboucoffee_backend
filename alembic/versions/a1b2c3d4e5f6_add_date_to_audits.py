"""Add date column to audits table

Revision ID: a1b2c3d4e5f6
Revises: f0a1b2c3d4e5
Create Date: 2026-03-26 19:39:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'f0a1b2c3d4e5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('audits', sa.Column('date', sa.DateTime(timezone=True), nullable=True))
    # Backfill existing audits: set date = created_at
    op.execute("UPDATE audits SET date = created_at WHERE date IS NULL")


def downgrade() -> None:
    op.drop_column('audits', 'date')
