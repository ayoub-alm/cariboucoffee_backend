
"""Add conformity thresholds table

Revision ID: a7b8c9d0e1f2
Revises: 0379b5725cee
Create Date: 2026-04-25 18:41:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a7b8c9d0e1f2'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    # Check if table exists before creating
    from sqlalchemy.engine.reflection import Inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    if 'conformity_thresholds' not in tables:
        op.create_table('conformity_thresholds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conforme_min', sa.Float(), nullable=True),
        sa.Column('partiel_min', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_conformity_thresholds_id'), 'conformity_thresholds', ['id'], unique=False)


def downgrade():
    from sqlalchemy.engine.reflection import Inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    if 'conformity_thresholds' in tables:
        op.drop_index(op.f('ix_conformity_thresholds_id'), table_name='conformity_thresholds')
        op.drop_table('conformity_thresholds')
