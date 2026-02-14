from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api import deps
from app.models.models import AuditCategory, AuditQuestion, User, UserRole
from app.schemas import schemas

router = APIRouter()

@router.get("", response_model=List[schemas.AuditCategoryResponse])
async def read_categories(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve audit categories.
    """
    query = select(AuditCategory).options(selectinload(AuditCategory.questions)).offset(skip).limit(limit)
    result = await db.execute(query)
    categories = result.scalars().all()
    return categories

@router.get("/{category_id}", response_model=schemas.AuditCategoryResponse)
async def read_category(
    *,
    db: AsyncSession = Depends(deps.get_db),
    category_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get category by ID.
    """
    query = select(AuditCategory).where(AuditCategory.id == category_id)
    result = await db.execute(query)
    category = result.scalars().first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return category

@router.post("", response_model=schemas.AuditCategoryResponse)
async def create_category(
    *,
    db: AsyncSession = Depends(deps.get_db),
    category_in: schemas.AuditCategoryCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new audit category.
    Only Admin can create.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    category = AuditCategory(
        name=category_in.name,
        description=category_in.description
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category

@router.put("/{category_id}", response_model=schemas.AuditCategoryResponse)
async def update_category(
    *,
    db: AsyncSession = Depends(deps.get_db),
    category_id: int,
    category_in: schemas.AuditCategoryCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update audit category.
    Only Admin can update.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    query = select(AuditCategory).where(AuditCategory.id == category_id)
    result = await db.execute(query)
    category = result.scalars().first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    category.name = category_in.name
    category.description = category_in.description
    
    await db.commit()
    await db.refresh(category)
    return category

@router.delete("/{category_id}")
async def delete_category(
    *,
    db: AsyncSession = Depends(deps.get_db),
    category_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Delete audit category.
    Only Admin can delete.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    query = select(AuditCategory).where(AuditCategory.id == category_id)
    result = await db.execute(query)
    category = result.scalars().first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    await db.delete(category)
    await db.commit()
    return {"ok": True}
