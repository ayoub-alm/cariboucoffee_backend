from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import datetime

from app.api import deps
from app.models.models import DailyTimeRecord, UserRole, User, Coffee
from app.schemas import schemas

router = APIRouter()

@router.get("", response_model=List[schemas.DailyTimeRecordResponse])
async def read_daily_logs(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve daily logs.
    """
    if current_user.role == UserRole.CONTROLLER:
        query = select(DailyTimeRecord).where(DailyTimeRecord.controller_id == current_user.id).offset(skip).limit(limit)
    elif current_user.role in [UserRole.ADMIN, UserRole.BOSS]:
        query = select(DailyTimeRecord).offset(skip).limit(limit)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    result = await db.execute(query)
    logs = result.scalars().all()
    return logs

@router.post("", response_model=schemas.DailyTimeRecordResponse)
async def create_daily_log(
    *,
    db: AsyncSession = Depends(deps.get_db),
    log_in: schemas.DailyTimeRecordCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new daily log (Controller only).
    """
    if current_user.role != UserRole.CONTROLLER and current_user.role != UserRole.ADMIN:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    # Check if a log already exists for this coffee and date
    query = select(DailyTimeRecord).where(
        DailyTimeRecord.coffee_id == log_in.coffee_id,
        DailyTimeRecord.date == log_in.date
    )
    result = await db.execute(query)
    existing_log = result.scalars().first()

    if existing_log:
        # Update existing record
        if log_in.opening_time is not None:
            existing_log.opening_time = log_in.opening_time
        if log_in.closing_time is not None:
            existing_log.closing_time = log_in.closing_time
        existing_log.controller_id = current_user.id  # Update last modified by
        log = existing_log
    else:
        # Create new record
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
    return log
