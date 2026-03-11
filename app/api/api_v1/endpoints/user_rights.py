"""
User Rights endpoint — CRUD permissions management.
Only ADMIN users can read or modify rights.
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api import deps
from app.models.models import User, UserRights, UserRole
from app.schemas import schemas

router = APIRouter()


def _rights_to_dict(r: UserRights) -> dict:
    return {
        "user_id": r.user_id,
        "coffees":    {"read": r.coffees_read,    "create": r.coffees_create,    "update": r.coffees_update,    "delete": r.coffees_delete},
        "audits":     {"read": r.audits_read,     "create": r.audits_create,     "update": r.audits_update,     "delete": r.audits_delete},
        "users":      {"read": r.users_read,      "create": r.users_create,      "update": r.users_update,      "delete": r.users_delete},
        "categories": {"read": r.categories_read, "create": r.categories_create, "update": r.categories_update, "delete": r.categories_delete},
        "questions":  {"read": r.questions_read,  "create": r.questions_create,  "update": r.questions_update,  "delete": r.questions_delete},
    }


async def _get_or_create_rights(db: AsyncSession, user_id: int) -> UserRights:
    result = await db.execute(select(UserRights).where(UserRights.user_id == user_id))
    rights = result.scalars().first()
    if not rights:
        rights = UserRights(user_id=user_id)
        db.add(rights)
        await db.flush()
    return rights


@router.get("/{user_id}")
async def get_user_rights(
    user_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Get CRUD permissions for a user (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    # Verify user exists
    result = await db.execute(select(User).where(User.id == user_id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    rights = await _get_or_create_rights(db, user_id)
    await db.commit()
    return _rights_to_dict(rights)


@router.put("/{user_id}")
async def update_user_rights(
    user_id: int,
    payload: schemas.UserRightsUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Update CRUD permissions for a user (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    # Verify user exists
    result = await db.execute(select(User).where(User.id == user_id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    rights = await _get_or_create_rights(db, user_id)

    # Apply each module block if provided
    for module in ("coffees", "audits", "users", "categories", "questions"):
        block = getattr(payload, module, None)
        if block is None:
            continue
        for action in ("read", "create", "update", "delete"):
            val = getattr(block, action, None)
            if val is not None:
                setattr(rights, f"{module}_{action}", val)

    await db.commit()
    return _rights_to_dict(rights)
