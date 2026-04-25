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

    query = (
        select(AuditCategory)
        .options(selectinload(AuditCategory.questions))
        .order_by(AuditCategory.display_order)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/reorder")
async def reorder_categories(
    *,
    db: AsyncSession = Depends(deps.get_db),
    body: schemas.ReorderRequest,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Bulk-update display_order for categories. Admin only."""
    has_update_rights = current_user.rights and current_user.rights.categories_update
    if current_user.role != UserRole.ADMIN and not has_update_rights:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    result = await db.execute(select(AuditCategory))
    cats = {c.id: c for c in result.scalars().all()}

    for item in body.items:
        if item.id in cats:
            cats[item.id].display_order = item.display_order

    await db.commit()
    return {"ok": True}


@router.get("/{category_id}", response_model=schemas.AuditCategoryResponse)
async def read_category(
    *,
    db: AsyncSession = Depends(deps.get_db),
    category_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    query = select(AuditCategory).where(AuditCategory.id == category_id).options(selectinload(AuditCategory.questions))
    result = await db.execute(query)
    category = result.scalars().first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.post("")
async def create_category(
    *,
    db: AsyncSession = Depends(deps.get_db),
    category_in: schemas.AuditCategoryCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    has_create_rights = current_user.rights and current_user.rights.categories_create
    if current_user.role != UserRole.ADMIN and not has_create_rights:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Auto-set display_order to max+1 if not provided
    count_result = await db.execute(select(AuditCategory))
    existing_count = len(count_result.scalars().all())

    category = AuditCategory(
        name=category_in.name,
        description=category_in.description,
        icon=category_in.icon,
        display_order=category_in.display_order if category_in.display_order else existing_count,
    )
    db.add(category)
    await db.commit()

    query = select(AuditCategory).where(AuditCategory.id == category.id).options(selectinload(AuditCategory.questions))
    result = await db.execute(query)
    return result.scalars().first()


@router.put("/{category_id}")
async def update_category(
    *,
    db: AsyncSession = Depends(deps.get_db),
    category_id: int,
    category_in: schemas.AuditCategoryCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    has_update_rights = current_user.rights and current_user.rights.categories_update
    if current_user.role != UserRole.ADMIN and not has_update_rights:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    query = select(AuditCategory).where(AuditCategory.id == category_id).options(selectinload(AuditCategory.questions))
    result = await db.execute(query)
    category = result.scalars().first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    category.name = category_in.name
    category.description = category_in.description
    category.icon = category_in.icon

    await db.commit()

    query = select(AuditCategory).where(AuditCategory.id == category_id).options(selectinload(AuditCategory.questions))
    result = await db.execute(query)
    return result.scalars().first()


@router.delete("/{category_id}")
async def delete_category(
    *,
    db: AsyncSession = Depends(deps.get_db),
    category_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    has_delete_rights = current_user.rights and current_user.rights.categories_delete
    if current_user.role != UserRole.ADMIN and not has_delete_rights:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    query = select(AuditCategory).where(AuditCategory.id == category_id)
    result = await db.execute(query)
    category = result.scalars().first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    await db.delete(category)
    await db.commit()
    return {"ok": True}
