"""Schedule (horaire) scoring based on compliant minutes within expected opening hours.

Now supports per-day schedules via CoffeeSchedule model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Coffee, CoffeeSchedule, DailyTimeRecord, ScheduleThreshold


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
    expected_opening: str   # for display purposes
    expected_closing: str   # for display purposes


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


def _date_to_day_of_week(log_date) -> int:
    """Convert a date to our day_of_week convention: 0=Dimanche, 1=Lundi ... 6=Samedi.
    Python's weekday(): 0=Monday ... 6=Sunday.
    """
    import datetime
    if isinstance(log_date, str):
        log_date = datetime.date.fromisoformat(log_date)
    python_weekday = log_date.weekday()  # 0=Monday, 6=Sunday
    # Convert: Sunday(6) -> 0, Monday(0) -> 1, ... Saturday(5) -> 6
    return (python_weekday + 1) % 7


def get_schedule_for_day(
    schedules: Optional[List["CoffeeSchedule"]],
    log_date,
) -> Optional["CoffeeSchedule"]:
    """Find the CoffeeSchedule matching the log's day of week."""
    if not schedules:
        return None
    day = _date_to_day_of_week(log_date)
    for s in schedules:
        if s.day_of_week == day:
            return s
    return None


def _conforme_result(expected_opening: str = "--:--", expected_closing: str = "--:--") -> ScheduleScoreResult:
    """Return a fully-conforme result (used for closed days or missing config)."""
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
        expected_opening=expected_opening,
        expected_closing=expected_closing,
    )


def compute_schedule_score(
    log: "DailyTimeRecord",
    coffee: Optional["Coffee"],
    thr: Optional["ScheduleThreshold"] = None,
    schedules: Optional[List["CoffeeSchedule"]] = None,
) -> ScheduleScoreResult:
    """
    Score = compliant minutes within the expected window.
    lost_minutes = late opening + early closing (minutes outside expected range).

    Priority for expected times:
    1. log.expected_opening / log.expected_closing (snapshot saved at record-creation)
       → used for all new records so future schedule changes never alter past scores.
    2. Live per-day CoffeeSchedule lookup  (fallback for legacy NULL records)
    3. Coffee.opening_time / Coffee.closing_time  (final fallback)
    """
    expected_opening: Optional[str] = None
    expected_closing: Optional[str] = None

    # ── 1. Use frozen snapshot when available (new records) ─────────────────
    snapshot_opening = getattr(log, "expected_opening", None)
    snapshot_closing = getattr(log, "expected_closing", None)

    if snapshot_opening and snapshot_closing:
        # Closed-day marker stored as the literal string "Fermé"
        if snapshot_opening == "Fermé":
            return _conforme_result("Fermé", "Fermé")
        expected_opening = snapshot_opening
        expected_closing = snapshot_closing

    else:
        # ── 2. Live per-day schedule lookup (legacy records with NULL snapshot) ─
        day_schedule = get_schedule_for_day(schedules, log.date) if schedules else None
        if day_schedule is None and coffee and hasattr(coffee, "schedules") and coffee.schedules:
            day_schedule = get_schedule_for_day(coffee.schedules, log.date)

        if day_schedule:
            if day_schedule.is_closed:
                return _conforme_result("Fermé", "Fermé")
            expected_opening = day_schedule.opening_time
            expected_closing = day_schedule.closing_time
        elif coffee:
            # ── 3. Static coffee times ─────────────────────────────────────
            expected_opening = coffee.opening_time
            expected_closing = coffee.closing_time

    if not expected_opening or not expected_closing:
        return _conforme_result(expected_opening or "--:--", expected_closing or "--:--")

    config_start = time_to_minutes(expected_opening)
    config_end = time_to_minutes(expected_closing)
    config_range = float(max(config_end - config_start, 0))

    if config_range <= 0:
        return _conforme_result(expected_opening, expected_closing)

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
            expected_opening=expected_opening,
            expected_closing=expected_closing,
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
        expected_opening=expected_opening,
        expected_closing=expected_closing,
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
        "expected_opening": result.expected_opening,
        "expected_closing": result.expected_closing,
    }
