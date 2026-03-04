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
    # Add ref column as nullable first (existing rows can't have a NOT NULL constraint
    # without a default, and we want to back-fill later)
    op.add_column('coffees', sa.Column('ref', sa.String(), nullable=True))

    # Back-fill existing rows with a generated ref like CAF-001, CAF-002, …
    op.execute("""
        UPDATE coffees
        SET ref = 'CAF-' || LPAD(id::text, 3, '0')
        WHERE ref IS NULL
    """)

    # Now add a unique index on ref
    op.create_index('ix_coffees_ref', 'coffees', ['ref'], unique=True)


def downgrade():
    op.drop_index('ix_coffees_ref', table_name='coffees')
    op.drop_column('coffees', 'ref')
