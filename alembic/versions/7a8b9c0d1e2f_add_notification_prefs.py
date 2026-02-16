"""add_notification_prefs

Revision ID: 7a8b9c0d1e2f
Revises: 5f3e2a1b9c8d
Create Date: 2026-02-14 23:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = '7a8b9c0d1e2f'
down_revision = '5f3e2a1b9c8d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    if 'users' in tables:
        columns = [c['name'] for c in inspector.get_columns('users')]
        if 'receive_daily_report' not in columns:
            op.add_column('users', sa.Column('receive_daily_report', sa.Boolean(), nullable=True, server_default='false'))
        if 'receive_weekly_report' not in columns:
            op.add_column('users', sa.Column('receive_weekly_report', sa.Boolean(), nullable=True, server_default='false'))
        if 'receive_monthly_report' not in columns:
            op.add_column('users', sa.Column('receive_monthly_report', sa.Boolean(), nullable=True, server_default='false'))


def downgrade() -> None:
    op.drop_column('users', 'receive_daily_report')
    op.drop_column('users', 'receive_weekly_report')
    op.drop_column('users', 'receive_monthly_report')
