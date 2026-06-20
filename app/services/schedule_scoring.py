"""Schedule (horaire) scoring based on compliant minutes within expected opening hours."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Coffee, DailyTimeRecord, ScheduleThreshold


@dataclass
class ScheduleScoreResult:
    score: float
    config_range: float
    late_minutes: float
    early_minutes: float
    lost_minutes: float
    is_late_opening: bool
    is_early_closing: bool
    status: str
    conformity_label: str


def time_to_minutes(t: str) -> int:
    """Convert 'HH:MM' string to total minutes."""
    try:
        h, m = map(int, t.split(":"))
        return h * 60 + m
    except Exception:
        return 0


def conformity_label_from_status(status: str) -> str:
    return {
        "green": "Conforme",
        "orange": "Partiel",
        "red": "Non-conforme",
    }.get(status, "Non-conforme")


def compute_status(
    late_minutes: float,
    early_minutes: float,
    thr: Optional["ScheduleThreshold"],
) -> str:
    """
    Conformity is based on opening/closing times vs expected hours.
    Uses the worst violation (latest opening or earliest closing) against configured limits.
    """
    green_max = thr.green_min if thr and thr.green_min is not None else 0.0
    orange_max = thr.orange_min if thr and thr.orange_min is not None else 60.0
    worst_violation = max(late_minutes, early_minutes)

    if worst_violation <= green_max:
        return "green"
    if worst_violation <= orange_max:
        return "orange"
    return "red"


def compute_schedule_score(
    log: "DailyTimeRecord",
    coffee: Optional["Coffee"],
    thr: Optional["ScheduleThreshold"] = None,
) -> ScheduleScoreResult:
    """
    Score = compliant minutes within the expected window.
    lost_minutes = late opening + early closing (minutes outside expected range).
    """
    if not coffee or not coffee.opening_time or not coffee.closing_time:
        return ScheduleScoreResult(
            score=0.0,
            config_range=0.0,
            late_minutes=0.0,
            early_minutes=0.0,
            lost_minutes=0.0,
            is_late_opening=False,
            is_early_closing=False,
            status="green",
            conformity_label="Conforme",
        )

    config_start = time_to_minutes(coffee.opening_time)
    config_end = time_to_minutes(coffee.closing_time)
    config_range = float(max(config_end - config_start, 0))

    if config_range <= 0:
        return ScheduleScoreResult(
            score=0.0,
            config_range=0.0,
            late_minutes=0.0,
            early_minutes=0.0,
            lost_minutes=0.0,
            is_late_opening=False,
            is_early_closing=False,
            status="green",
            conformity_label="Conforme",
        )

    if not log.opening_time or not log.closing_time:
        status = "red"
        return ScheduleScoreResult(
            score=0.0,
            config_range=config_range,
            late_minutes=0.0,
            early_minutes=0.0,
            lost_minutes=config_range,
            is_late_opening=not bool(log.opening_time),
            is_early_closing=not bool(log.closing_time),
            status=status,
            conformity_label=conformity_label_from_status(status),
        )

    actual_start = time_to_minutes(log.opening_time)
    actual_end = time_to_minutes(log.closing_time)

    late_minutes = float(max(0, actual_start - config_start))
    early_minutes = float(max(0, config_end - actual_end))
    lost_minutes = late_minutes + early_minutes
    score = max(config_range - lost_minutes, 0.0)
    is_late_opening = late_minutes > 0
    is_early_closing = early_minutes > 0
    status = compute_status(late_minutes, early_minutes, thr)

    return ScheduleScoreResult(
        score=round(score, 2),
        config_range=config_range,
        late_minutes=round(late_minutes, 2),
        early_minutes=round(early_minutes, 2),
        lost_minutes=round(lost_minutes, 2),
        is_late_opening=is_late_opening,
        is_early_closing=is_early_closing,
        status=status,
        conformity_label=conformity_label_from_status(status),
    )


def score_result_to_dict(result: ScheduleScoreResult) -> dict:
    return {
        "score": result.score,
        "config_range": result.config_range,
        "late_minutes": result.late_minutes,
        "early_minutes": result.early_minutes,
        "lost_minutes": result.lost_minutes,
        "is_late_opening": result.is_late_opening,
        "is_early_closing": result.is_early_closing,
        "status": result.status,
        "conformity_label": result.conformity_label,
    }
