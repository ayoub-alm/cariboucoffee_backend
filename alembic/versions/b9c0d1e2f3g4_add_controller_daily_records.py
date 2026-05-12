"""Add controller and daily records

Revision ID: b9c0d1e2f3g4
Revises: a8b9c0d1e2f3
Create Date: 2026-05-11 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b9c0d1e2f3g4'
down_revision = 'a8b9c0d1e2f3'
branch_labels = None
depends_on = None


def upgrade():
    # Update Enum for UserRole
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'CONTROLLER'")

    # Add columns to Coffee
    op.add_column('coffees', sa.Column('opening_time', sa.String(), nullable=True))
    op.add_column('coffees', sa.Column('closing_time', sa.String(), nullable=True))

    # Create DailyTimeRecord table
    op.execute("DROP TABLE IF EXISTS daily_time_records CASCADE")
    op.create_table('daily_time_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('opening_time', sa.String(), nullable=True),
        sa.Column('closing_time', sa.String(), nullable=True),
        sa.Column('coffee_id', sa.Integer(), nullable=False),
        sa.Column('controller_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['coffee_id'], ['coffees.id'], ),
        sa.ForeignKeyConstraint(['controller_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_daily_time_records_id'), 'daily_time_records', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_daily_time_records_id'), table_name='daily_time_records')
    op.drop_table('daily_time_records')
    op.drop_column('coffees', 'closing_time')
    op.drop_column('coffees', 'opening_time')
