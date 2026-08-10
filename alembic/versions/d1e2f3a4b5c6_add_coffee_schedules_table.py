"""Add coffee_schedules table for per-day opening/closing times

Revision ID: d1e2f3a4b5c6
Revises: c3d4e5f6a7b8
Create Date: 2026-07-23 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d1e2f3a4b5c6"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT to_regclass('public.coffee_schedules')")).scalar()
    
    if not result:
        op.create_table(
            "coffee_schedules",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("coffee_id", sa.Integer(), sa.ForeignKey("coffees.id"), nullable=False),
            sa.Column("day_of_week", sa.Integer(), nullable=False),
            sa.Column("is_closed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column("opening_time", sa.String(), nullable=True),
            sa.Column("closing_time", sa.String(), nullable=True),
        )
        op.create_index("ix_coffee_schedules_id", "coffee_schedules", ["id"])
        op.create_index("ix_coffee_schedules_coffee_day", "coffee_schedules", ["coffee_id", "day_of_week"], unique=True)

        # Migrate existing fixed opening/closing times into 7-day schedules
        coffees = conn.execute(sa.text("SELECT id, opening_time, closing_time FROM coffees")).fetchall()
        for coffee in coffees:
            coffee_id = coffee[0]
            opening = coffee[1]
            closing = coffee[2]
            if opening or closing:
                for day in range(7):
                    conn.execute(
                        sa.text(
                            "INSERT INTO coffee_schedules (coffee_id, day_of_week, is_closed, opening_time, closing_time) "
                            "VALUES (:coffee_id, :day, false, :opening, :closing)"
                        ),
                        {"coffee_id": coffee_id, "day": day, "opening": opening, "closing": closing}
                    )


def downgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT to_regclass('public.coffee_schedules')")).scalar()
    if result:
        op.drop_index("ix_coffee_schedules_coffee_day", table_name="coffee_schedules")
        op.drop_index("ix_coffee_schedules_id", table_name="coffee_schedules")
        op.drop_table("coffee_schedules")
