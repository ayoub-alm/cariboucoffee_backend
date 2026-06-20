"""Convert schedule threshold defaults from legacy percentage values to minutes."""

from alembic import op


revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Legacy values were percentages (100 = green, 90 = orange).
    # New semantics: max tolerable lost minutes (0 = green, 60 = orange).
    op.execute(
        """
        UPDATE schedule_thresholds
        SET green_min = 0.0, orange_min = 60.0
        WHERE green_min >= 1.0 AND green_min <= 100.0
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE schedule_thresholds
        SET green_min = 100.0, orange_min = 90.0
        WHERE green_min = 0.0 AND orange_min = 60.0
        """
    )
