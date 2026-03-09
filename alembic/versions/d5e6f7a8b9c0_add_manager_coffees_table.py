"""Add manager_coffees many-to-many table

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-03-06 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'd5e6f7a8b9c0'
down_revision = 'c4d5e6f7a8b9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'manager_coffees',
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('coffee_id', sa.Integer(), sa.ForeignKey('coffees.id'), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table('manager_coffees')
