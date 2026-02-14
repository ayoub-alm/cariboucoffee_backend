"""safe_create_tables_and_add_columns

Revision ID: 5f3e2a1b9c8d
Revises: 34a12dce0b42
Create Date: 2026-02-14 23:25:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = '5f3e2a1b9c8d'
down_revision = '34a12dce0b42'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    # 1. audit_categories
    if 'audit_categories' not in tables:
        op.create_table('audit_categories',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=True),
            sa.Column('description', sa.String(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )
        op.create_index(op.f('ix_audit_categories_id'), 'audit_categories', ['id'], unique=False)

    # 2. coffees
    if 'coffees' not in tables:
        op.create_table('coffees',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=True),
            sa.Column('location', sa.String(), nullable=True),
            sa.Column('active', sa.Boolean(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_coffees_id'), 'coffees', ['id'], unique=False)
        op.create_index(op.f('ix_coffees_name'), 'coffees', ['name'], unique=False)

    # 3. users
    if 'users' not in tables:
        op.create_table('users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('email', sa.String(), nullable=True),
            sa.Column('hashed_password', sa.String(), nullable=True),
            sa.Column('full_name', sa.String(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('role', sa.Enum('ADMIN', 'AUDITOR', 'VIEWER', name='userrole'), nullable=True),
            sa.Column('coffee_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['coffee_id'], ['coffees.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
        op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # 4. audit_questions
    if 'audit_questions' not in tables:
        op.create_table('audit_questions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('text', sa.String(), nullable=True),
            sa.Column('weight', sa.Integer(), nullable=True),
            sa.Column('category_id', sa.Integer(), nullable=True),
            sa.Column('correct_answer', sa.String(), nullable=True),
            sa.Column('na_score', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['category_id'], ['audit_categories.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_audit_questions_id'), 'audit_questions', ['id'], unique=False)
    else:
        # Check for columns that might be missing if table was created by older logic
        existing_columns = [c['name'] for c in inspector.get_columns('audit_questions')]
        if 'correct_answer' not in existing_columns:
            op.add_column('audit_questions', sa.Column('correct_answer', sa.String(), nullable=True, server_default='oui'))
        if 'na_score' not in existing_columns:
             op.add_column('audit_questions', sa.Column('na_score', sa.Integer(), nullable=True, server_default='0'))


    # 5. audits
    if 'audits' not in tables:
        op.create_table('audits',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('score', sa.Float(), nullable=True),
            sa.Column('coffee_id', sa.Integer(), nullable=True),
            sa.Column('auditor_id', sa.Integer(), nullable=True),
            sa.Column('shift', sa.String(), nullable=True),
            sa.Column('staff_present', sa.String(), nullable=True),
            sa.Column('actions_correctives', sa.String(), nullable=True),
            sa.Column('training_needs', sa.String(), nullable=True),
            sa.Column('purchases', sa.String(), nullable=True),
            sa.ForeignKeyConstraint(['auditor_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['coffee_id'], ['coffees.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_audits_id'), 'audits', ['id'], unique=False)

    # 6. audit_answers
    if 'audit_answers' not in tables:
        op.create_table('audit_answers',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('value', sa.Integer(), nullable=True),
            sa.Column('choice', sa.String(), nullable=True),
            sa.Column('comment', sa.String(), nullable=True),
            sa.Column('audit_id', sa.Integer(), nullable=True),
            sa.Column('question_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['audit_id'], ['audits.id'], ),
            sa.ForeignKeyConstraint(['question_id'], ['audit_questions.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_audit_answers_id'), 'audit_answers', ['id'], unique=False)
    else:
        # Table exists, check for column 'choice'
        columns = [c['name'] for c in inspector.get_columns('audit_answers')]
        if 'choice' not in columns:
            op.add_column('audit_answers', sa.Column('choice', sa.String(), nullable=True))


def downgrade() -> None:
    pass
