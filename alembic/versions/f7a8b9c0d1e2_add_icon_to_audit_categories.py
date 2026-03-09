"""Add icon column to audit_categories table

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-03-06 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'f7a8b9c0d1e2'
down_revision = 'e6f7a8b9c0d1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('audit_categories', sa.Column('icon', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('audit_categories', 'icon')
