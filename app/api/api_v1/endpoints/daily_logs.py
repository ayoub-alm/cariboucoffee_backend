from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import datetime

from app.api import deps
from app.models.models import DailyTimeRecord, ScheduleThreshold, UserRole, User, Coffee
from app.schemas import schemas

router = APIRouter()


def _time_to_minutes(t: str) -> int:
    """Convert 'HH:MM' string to total minutes."""
    try:
        h, m = map(int, t.split(":"))
        return h * 60 + m
    except Exception:
        return 0


def _compute_score(log: DailyTimeRecord, coffee: Optional[Coffee]) -> float:
    """Compute score as (real_range / config_range) * 100, capped at 100."""
    if not coffee:
        return 100.0
    if not coffee.opening_time or not coffee.closing_time:
        return 100.0
    if not log.opening_time or not log.closing_time:
        return 0.0

    config_start = _time_to_minutes(coffee.opening_time)
    config_end   = _time_to_minutes(coffee.closing_time)
    config_range = config_end - config_start

    real_start = _time_to_minutes(log.opening_time)
    real_end   = _time_to_minutes(log.closing_time)
    real_range = real_end - real_start

    if config_range <= 0:
        return 100.0

    percentage = (real_range / config_range) * 100.0
    return min(round(percentage, 2), 100.0)


def _compute_status(score: float, thr: Optional[ScheduleThreshold]) -> str:
    green_min  = thr.green_min  if thr else 100.0
    orange_min = thr.orange_min if thr else 90.0
    if score >= green_min:
        return "green"
    if score >= orange_min:
        return "orange"
    return "red"


@router.get("", response_model=List[schemas.DailyTimeRecordEnriched])
async def read_daily_logs(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 1000,
    coffee_id: Optional[int] = None,
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Retrieve daily logs with backend-computed score and status."""
    if current_user.role not in [UserRole.ADMIN, UserRole.BOSS, UserRole.CONTROLLER]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    # Load schedule thresholds once
    thr_result = await db.execute(select(ScheduleThreshold).limit(1))
    thr = thr_result.scalars().first()

    # Load all coffees into a dict for fast lookup
    coffees_result = await db.execute(select(Coffee))
    coffees = {c.id: c for c in coffees_result.scalars().all()}

    query = select(DailyTimeRecord)
    if coffee_id is not None:
        query = query.where(DailyTimeRecord.coffee_id == coffee_id)
    if start_date is not None:
        query = query.where(DailyTimeRecord.date >= start_date)
    if end_date is not None:
        query = query.where(DailyTimeRecord.date <= end_date)
    query = query.order_by(DailyTimeRecord.date.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    logs = result.scalars().all()

    enriched = []
    for log in logs:
        coffee = coffees.get(log.coffee_id)
        score  = _compute_score(log, coffee)
        status_label = _compute_status(score, thr)
        enriched.append({
            "id":            log.id,
            "date":          log.date,
            "opening_time":  log.opening_time,
            "closing_time":  log.closing_time,
            "coffee_id":     log.coffee_id,
            "controller_id": log.controller_id,
            "score":         score,
            "status":        status_label,
        })

    return enriched


@router.post("", response_model=schemas.DailyTimeRecordEnriched)
async def create_daily_log(
    *,
    db: AsyncSession = Depends(deps.get_db),
    log_in: schemas.DailyTimeRecordCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Create or update a daily log, returning the record with computed score."""
    if current_user.role not in [UserRole.CONTROLLER, UserRole.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    # Load threshold
    thr_result = await db.execute(select(ScheduleThreshold).limit(1))
    thr = thr_result.scalars().first()

    # Load coffee
    coffee_result = await db.execute(select(Coffee).where(Coffee.id == log_in.coffee_id))
    coffee = coffee_result.scalars().first()

    # Check existing log
    query = select(DailyTimeRecord).where(
        DailyTimeRecord.coffee_id == log_in.coffee_id,
        DailyTimeRecord.date == log_in.date
    )
    result = await db.execute(query)
    existing_log = result.scalars().first()

    if existing_log:
        if log_in.opening_time is not None:
            existing_log.opening_time = log_in.opening_time
        if log_in.closing_time is not None:
            existing_log.closing_time = log_in.closing_time
        existing_log.controller_id = current_user.id
        log = existing_log
    else:
        log = DailyTimeRecord(
            date=log_in.date,
            opening_time=log_in.opening_time,
            closing_time=log_in.closing_time,
            coffee_id=log_in.coffee_id,
            controller_id=current_user.id
        )
        db.add(log)

    await db.commit()
    await db.refresh(log)

    score = _compute_score(log, coffee)
    status_label = _compute_status(score, thr)

    return {
        "id":            log.id,
        "date":          log.date,
        "opening_time":  log.opening_time,
        "closing_time":  log.closing_time,
        "coffee_id":     log.coffee_id,
        "controller_id": log.controller_id,
        "score":         score,
        "status":        status_label,
    }
