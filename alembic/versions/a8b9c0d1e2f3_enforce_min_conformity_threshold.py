"""Enforce minimum conformity threshold values

Revision ID: a8b9c0d1e2f3
Revises: a7b8c9d0e1f2
Create Date: 2026-05-02 21:28:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a8b9c0d1e2f3'
down_revision = 'a7b8c9d0e1f2'
branch_labels = None
depends_on = None


def upgrade():
    # Update existing NULL values or values < 1.0 to 1.0 to prevent calculation crashes
    op.execute(
        "UPDATE conformity_thresholds "
        "SET conforme_min = 1.0 "
        "WHERE conforme_min IS NULL OR conforme_min < 1.0"
    )
    op.execute(
        "UPDATE conformity_thresholds "
        "SET partiel_min = 1.0 "
        "WHERE partiel_min IS NULL OR partiel_min < 1.0"
    )


def downgrade():
    # Data migration only; no schema changes to downgrade.
    pass
