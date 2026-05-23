"""Add schedule_thresholds table

Revision ID: b2c3d4e5f6a7
Revises: a8b9c0d1e2f3
Create Date: 2026-05-23 11:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'b9c0d1e2f3g4'
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy.engine.reflection import Inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    if 'schedule_thresholds' not in tables:
        op.create_table(
            'schedule_thresholds',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('green_min',  sa.Float(), nullable=True, server_default='100.0'),
            sa.Column('orange_min', sa.Float(), nullable=True, server_default='90.0'),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_schedule_thresholds_id'), 'schedule_thresholds', ['id'], unique=False)

        # Seed default row
        op.execute(
            "INSERT INTO schedule_thresholds (green_min, orange_min) VALUES (100.0, 90.0)"
        )


def downgrade():
    from sqlalchemy.engine.reflection import Inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    if 'schedule_thresholds' in tables:
        op.drop_index(op.f('ix_schedule_thresholds_id'), table_name='schedule_thresholds')
        op.drop_table('schedule_thresholds')
