"""Add user_rights table for CRUD permissions

Revision ID: e8f9a0b1c2d3
Revises: d5e6f7a8b9c0
Create Date: 2026-03-11 03:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'e8f9a0b1c2d3'
down_revision = 'f7a8b9c0d1e2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not inspector.has_table('user_rights'):
        op.create_table(
            'user_rights',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, unique=True),

            # Coffees
            sa.Column('coffees_read',   sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('coffees_create', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('coffees_update', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('coffees_delete', sa.Boolean(), nullable=False, server_default='false'),

            # Audits
            sa.Column('audits_read',   sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('audits_create', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('audits_update', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('audits_delete', sa.Boolean(), nullable=False, server_default='false'),

            # Users
            sa.Column('users_read',   sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('users_create', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('users_update', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('users_delete', sa.Boolean(), nullable=False, server_default='false'),

            # Categories
            sa.Column('categories_read',   sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('categories_create', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('categories_update', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('categories_delete', sa.Boolean(), nullable=False, server_default='false'),

            # Questions
            sa.Column('questions_read',   sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('questions_create', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('questions_update', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('questions_delete', sa.Boolean(), nullable=False, server_default='false'),
        )


def downgrade() -> None:
    op.drop_table('user_rights')
