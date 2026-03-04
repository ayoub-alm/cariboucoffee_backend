"""Add ref column to coffees

Revision ID: b1c2d3e4f5a6
Revises: 0379b5725cee
Create Date: 2026-03-04 04:23:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1c2d3e4f5a6'
down_revision = '0379b5725cee'
branch_labels = None
depends_on = None


def upgrade():
    # Use IF NOT EXISTS so the migration is safe to run even if the column
    # was already added manually (e.g. via a direct SQL fix on the server).
    op.execute("""
        ALTER TABLE coffees
        ADD COLUMN IF NOT EXISTS ref VARCHAR
    """)

    # Back-fill any rows that still have NULL ref
    op.execute("""
        UPDATE coffees
        SET ref = 'CAF-' || LPAD(id::text, 3, '0')
        WHERE ref IS NULL
    """)

    # Create unique index only if it doesn't already exist
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_coffees_ref ON coffees (ref)
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_coffees_ref")
    op.execute("ALTER TABLE coffees DROP COLUMN IF EXISTS ref")
