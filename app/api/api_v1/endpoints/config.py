from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api import deps
from app.models.models import ConformityThreshold, User, UserRole
from app.schemas import schemas

router = APIRouter()

@router.get("/conformity", response_model=schemas.ConformityThresholdResponse)
async def get_conformity_thresholds(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get conformity thresholds.
    """
    result = await db.execute(select(ConformityThreshold).limit(1))
    thresholds = result.scalars().first()
    
    if not thresholds:
        # Create default if not exists
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
    """
    Update conformity thresholds. Only Admins.
    """
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
        setattr(thresholds, field, value)
        
    db.add(thresholds)
    await db.commit()
    await db.refresh(thresholds)
    return thresholds
