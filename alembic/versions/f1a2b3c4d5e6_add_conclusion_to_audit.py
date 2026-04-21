"""Add conclusion column to audits

Revision ID: f1a2b3c4d5e6
Revises: a1b2c3d4e5f6
Create Date: 2026-04-21 23:42:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    if 'audits' in tables:
        columns = [c['name'] for c in inspector.get_columns('audits')]
        if 'conclusion' not in columns:
            op.add_column('audits', sa.Column('conclusion', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('audits', 'conclusion')
