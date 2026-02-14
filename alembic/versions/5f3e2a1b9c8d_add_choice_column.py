"""add choice column

Revision ID: 5f3e2a1b9c8d
Revises: 34a12dce0b42
Create Date: 2026-02-14 23:25:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '5f3e2a1b9c8d'
down_revision = '34a12dce0b42'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('audit_answers', sa.Column('choice', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('audit_answers', 'choice')
