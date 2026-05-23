from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api import deps
from app.models.models import ConformityThreshold, ScheduleThreshold, User, UserRole
from app.schemas import schemas

router = APIRouter()

# ── Audit conformity thresholds ─────────────────────────────────────────────

@router.get("/conformity", response_model=schemas.ConformityThresholdResponse)
async def get_conformity_thresholds(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Get conformity thresholds."""
    result = await db.execute(select(ConformityThreshold).limit(1))
    thresholds = result.scalars().first()
    
    if not thresholds:
        thresholds = ConformityThreshold(conforme_min=90.0, partiel_min=70.0)
        db.add(thresholds)
        await db.commit()
        await db.refresh(thresholds)
        
    return thresholds

@router.patch("/conformity", response_model=schemas.ConformityThresholdResponse)
async def update_conformity_thresholds(
    *,
    db: AsyncSession = Depends(deps.get_db),
    threshold_in: schemas.ConformityThresholdUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Update conformity thresholds. Only Admins."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
        
    result = await db.execute(select(ConformityThreshold).limit(1))
    thresholds = result.scalars().first()
    
    if not thresholds:
        thresholds = ConformityThreshold()
        db.add(thresholds)
        
    update_data = threshold_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is None or value < 1.0:
            value = 1.0
        setattr(thresholds, field, value)
        
    db.add(thresholds)
    await db.commit()
    await db.refresh(thresholds)
    return thresholds


# ── Schedule (horaire) thresholds ────────────────────────────────────────────

@router.get("/schedule-thresholds", response_model=schemas.ScheduleThresholdResponse)
async def get_schedule_thresholds(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Return the current schedule score thresholds (readable by all authenticated users)."""
    result = await db.execute(select(ScheduleThreshold).limit(1))
    thr = result.scalars().first()

    if not thr:
        thr = ScheduleThreshold(green_min=100.0, orange_min=90.0)
        db.add(thr)
        await db.commit()
        await db.refresh(thr)

    return thr


@router.patch("/schedule-thresholds", response_model=schemas.ScheduleThresholdResponse)
async def update_schedule_thresholds(
    *,
    db: AsyncSession = Depends(deps.get_db),
    threshold_in: schemas.ScheduleThresholdUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Update schedule score thresholds. Admin only."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )

    result = await db.execute(select(ScheduleThreshold).limit(1))
    thr = result.scalars().first()

    if not thr:
        thr = ScheduleThreshold()
        db.add(thr)

    update_data = threshold_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(thr, field, value)

    db.add(thr)
    await db.commit()
    await db.refresh(thr)
    return thr
