"""Add expected_opening and expected_closing snapshot columns to daily_time_records

Revision ID: e1f2a3b4c5d6
Revises: b9c0d1e2f3g4
Create Date: 2026-08-10 23:34:00.000000

These columns snapshot the café's scheduled hours at record-creation time so that
future schedule changes never retroactively alter historical scores.
Existing rows will have NULL, which causes the scoring service to fall back to the
current live-schedule lookup (preserving today's behavior for old records).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1f2a3b4c5d6'
down_revision = 'b9c0d1e2f3g4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('daily_time_records',
        sa.Column('expected_opening', sa.String(), nullable=True))
    op.add_column('daily_time_records',
        sa.Column('expected_closing', sa.String(), nullable=True))


def downgrade():
    op.drop_column('daily_time_records', 'expected_closing')
    op.drop_column('daily_time_records', 'expected_opening')
