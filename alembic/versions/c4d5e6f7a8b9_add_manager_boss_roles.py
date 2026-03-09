"""Add MANAGER and BOSS roles to UserRole enum

Revision ID: c4d5e6f7a8b9
Revises: b1c2d3e4f5a6
Create Date: 2026-03-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'c4d5e6f7a8b9'
down_revision = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'MANAGER'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'BOSS'")


def downgrade() -> None:
    pass
