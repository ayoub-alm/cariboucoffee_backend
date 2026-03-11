"""Add display_order to audit_categories and audit_questions

Revision ID: f0a1b2c3d4e5
Revises: e8f9a0b1c2d3
Create Date: 2026-03-11 03:25:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'f0a1b2c3d4e5'
down_revision = 'e8f9a0b1c2d3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    cat_cols = [c['name'] for c in inspector.get_columns('audit_categories')]
    if 'display_order' not in cat_cols:
        op.add_column('audit_categories', sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'))
        # Seed existing rows with their current id as order
        op.execute("UPDATE audit_categories SET display_order = id")

    q_cols = [c['name'] for c in inspector.get_columns('audit_questions')]
    if 'display_order' not in q_cols:
        op.add_column('audit_questions', sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'))
        op.execute("UPDATE audit_questions SET display_order = id")


def downgrade() -> None:
    op.drop_column('audit_questions', 'display_order')
    op.drop_column('audit_categories', 'display_order')
