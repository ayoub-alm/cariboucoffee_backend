from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api import deps
from app.models.models import Coffee, UserRole, User
from app.schemas import schemas

router = APIRouter()

@router.get("", response_model=List[schemas.CoffeeResponse])
async def read_coffees(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve coffees.
    """
    # Check permissions
    has_read_rights = current_user.rights and current_user.rights.coffees_read
    if current_user.role not in (UserRole.ADMIN, UserRole.BOSS, UserRole.MANAGER) and not has_read_rights:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    query = select(Coffee).offset(skip).limit(limit)
    result = await db.execute(query)
    coffees = result.scalars().all()
    
    if not coffees:
        # Seed default data
        default_shops = [
            {"name": "Caribou ANFA", "location": "Anfa"},
            {"name": "Caribou CASA VOYAGEUR", "location": "Casa Voyageur"},
            {"name": "Caribou MAARIF", "location": "Maarif"},
            {"name": "Caribou RABAT AGDAL", "location": "Rabat Agdal"}
        ]
        new_coffees = []
        for shop in default_shops:
            coffee = Coffee(name=shop["name"], location=shop["location"], active=True)
            db.add(coffee)
            new_coffees.append(coffee)
        await db.commit()
        for c in new_coffees:
            await db.refresh(c)
        return new_coffees

    return coffees

@router.post("", response_model=schemas.CoffeeResponse)
async def create_coffee(
    *,
    db: AsyncSession = Depends(deps.get_db),
    coffee_in: schemas.CoffeeCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new coffee.
    """
    has_create_rights = current_user.rights and current_user.rights.coffees_create
    if current_user.role != UserRole.ADMIN and not has_create_rights:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    ref = coffee_in.ref
    if not ref:
        # Count existing coffees to build the next ref
        from sqlalchemy import func as sa_func
        count_result = await db.execute(select(sa_func.count(Coffee.id)))
        count = count_result.scalar() or 0
        ref = f"CAF-{(count + 1):03d}"

    coffee = Coffee(
        ref=ref,
        name=coffee_in.name,
        location=coffee_in.location,
        active=coffee_in.active
    )
    db.add(coffee)
    await db.commit()
    await db.refresh(coffee)
    return coffee

@router.put("/{coffee_id}", response_model=schemas.CoffeeResponse)
async def update_coffee(
    *,
    db: AsyncSession = Depends(deps.get_db),
    coffee_id: int,
    coffee_in: schemas.CoffeeUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update a coffee.
    """
    has_update_rights = current_user.rights and current_user.rights.coffees_update
    if current_user.role != UserRole.ADMIN and not has_update_rights:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    query = select(Coffee).where(Coffee.id == coffee_id)
    result = await db.execute(query)
    coffee = result.scalars().first()
    if not coffee:
        raise HTTPException(status_code=404, detail="Coffee not found")
        
    update_data = coffee_in.model_dump(exclude_unset=True) 
    for field, value in update_data.items():
        setattr(coffee, field, value)
        
    db.add(coffee)
    await db.commit()
    await db.refresh(coffee)
    return coffee

@router.delete("/{coffee_id}")
async def delete_coffee(
    *,
    db: AsyncSession = Depends(deps.get_db),
    coffee_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Delete a coffee.
    """
    has_delete_rights = current_user.rights and current_user.rights.coffees_delete
    if current_user.role != UserRole.ADMIN and not has_delete_rights:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    query = select(Coffee).where(Coffee.id == coffee_id)
    result = await db.execute(query)
    coffee = result.scalars().first()
    if not coffee:
        raise HTTPException(status_code=404, detail="Coffee not found")
        
    await db.delete(coffee)
    await db.commit()
    return {"message": "Coffee deleted successfully", "id": coffee_id}
