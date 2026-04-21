from typing import Any, List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api import deps
from app.models.models import User, UserRole, Coffee, UserRights
from app.schemas import schemas
from app.core.security import get_password_hash, verify_password
from app.services.notification import send_user_report

router = APIRouter()


def _user_to_response(user: User) -> dict:
    r = user.rights
    permissions = None
    if r:
        permissions = {
            "coffees":    {"read": r.coffees_read,    "create": r.coffees_create,    "update": r.coffees_update,    "delete": r.coffees_delete},
            "audits":     {"read": r.audits_read,     "create": r.audits_create,     "update": r.audits_update,     "delete": r.audits_delete},
            "users":      {"read": r.users_read,      "create": r.users_create,      "update": r.users_update,      "delete": r.users_delete},
            "categories": {"read": r.categories_read, "create": r.categories_create, "update": r.categories_update, "delete": r.categories_delete},
            "questions":  {"read": r.questions_read,  "create": r.questions_create,  "update": r.questions_update,  "delete": r.questions_delete},
        }
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "role": user.role,
        "coffee_id": user.coffee_id,
        "receive_daily_report": user.receive_daily_report,
        "receive_weekly_report": user.receive_weekly_report,
        "receive_monthly_report": user.receive_monthly_report,
        "managed_coffee_ids": [c.id for c in user.managed_coffees] if user.managed_coffees else [],
        "permissions": permissions,
    }


async def _load_user(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(
        select(User)
        .options(selectinload(User.managed_coffees), selectinload(User.rights))
        .where(User.id == user_id)
    )
    return result.scalars().first()


@router.get("/me")
async def read_user_me(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    user = await _load_user(db, current_user.id)
    return _user_to_response(user)


@router.patch("/me/password")
async def update_my_password(
    body: schemas.PasswordChange,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Change the current user's password. Requires current password."""
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mot de passe actuel incorrect")
    current_user.hashed_password = get_password_hash(body.new_password)
    await db.commit()
    return {"message": "Mot de passe mis à jour"}


@router.patch("/{user_id}/password")
async def set_user_password(
    user_id: int,
    body: schemas.PasswordReset,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Admin sets a user's password (reset without current password)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges")
    user = await _load_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.hashed_password = get_password_hash(body.new_password)
    await db.commit()
    return {"message": "Mot de passe mis à jour"}


@router.get("")
async def read_users(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    has_read_rights = current_user.rights and current_user.rights.users_read
    if current_user.role != UserRole.ADMIN and not has_read_rights:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges")
    result = await db.execute(
        select(User)
        .options(selectinload(User.managed_coffees), selectinload(User.rights))
        .offset(skip)
        .limit(limit)
    )
    users = result.scalars().all()
    return [_user_to_response(u) for u in users]


@router.get("/{user_id}")
async def read_user_by_id(
    user_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    has_read_rights = current_user.rights and current_user.rights.users_read
    if current_user.role != UserRole.ADMIN and current_user.id != user_id and not has_read_rights:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges")
    user = await _load_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_response(user)


async def _sync_managed_coffees(db: AsyncSession, user: User, coffee_ids: List[int]):
    if coffee_ids is None:
        return
    result = await db.execute(select(Coffee).where(Coffee.id.in_(coffee_ids)))
    coffees = result.scalars().all()
    user.managed_coffees = list(coffees)


@router.post("")
async def create_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_in: schemas.UserCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    has_create_rights = current_user.rights and current_user.rights.users_create
    if current_user.role != UserRole.ADMIN and not has_create_rights:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges")

    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="A user with this email already exists")

    # Fetch managed coffees beforehand to avoid lazy-loading issues after db.add()
    managed_coffees = []
    if user_in.managed_coffee_ids:
        c_result = await db.execute(select(Coffee).where(Coffee.id.in_(user_in.managed_coffee_ids)))
        managed_coffees = list(c_result.scalars().all())

    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        is_active=True,
        coffee_id=user_in.coffee_id,
        managed_coffees=managed_coffees
    )
    db.add(user)
    
    # Defaults based on role
    if user.role == UserRole.ADMIN:
        # Admins don't strictly need a UserRights row as the guard handles it, 
        # but let's create a full-access object for consistency if needed.
        # Actually, let the model/default handle it or create explicit rights here.
        pass

    await db.commit()
    user = await _load_user(db, user.id)
    return _user_to_response(user)



@router.put("/{user_id}")
async def update_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_id: int,
    user_in: schemas.UserUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    has_update_rights = current_user.rights and current_user.rights.users_update
    if current_user.role != UserRole.ADMIN and not has_update_rights:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges")

    user = await _load_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_in.email is not None:
        user.email = user_in.email
    if user_in.password:
        user.hashed_password = get_password_hash(user_in.password)
    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.role is not None:
        user.role = user_in.role
    if user_in.coffee_id is not None:
        user.coffee_id = user_in.coffee_id
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    if user_in.receive_daily_report is not None:
        user.receive_daily_report = user_in.receive_daily_report
    if user_in.receive_weekly_report is not None:
        user.receive_weekly_report = user_in.receive_weekly_report
    if user_in.receive_monthly_report is not None:
        user.receive_monthly_report = user_in.receive_monthly_report

    if user_in.managed_coffee_ids is not None:
        await _sync_managed_coffees(db, user, user_in.managed_coffee_ids)

    await db.commit()
    user = await _load_user(db, user.id)
    return _user_to_response(user)


@router.delete("/{user_id}")
async def delete_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    has_delete_rights = current_user.rights and current_user.rights.users_delete
    if current_user.role != UserRole.ADMIN and not has_delete_rights:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges")

    user = await _load_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()
    return {"message": "User deleted successfully", "id": user_id}


@router.post("/{user_id}/send-report")
async def trigger_user_report(
    user_id: int,
    days: int = Body(..., embed=True),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """Trigger an instant email report for a user."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges")
    
    user = await _load_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    try:
        await send_user_report(user_id, days)
        return {"message": f"Rapport ({days} jours) envoyé avec succès à {user.email}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'envoi de l'email: {str(e)}")
