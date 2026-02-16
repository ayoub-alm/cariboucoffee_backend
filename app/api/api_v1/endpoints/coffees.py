from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api import deps
from app.models.models import Coffee, UserRole
from app.schemas import schemas

router = APIRouter()

@router.get("", response_model=List[schemas.CoffeeResponse])
async def read_coffees(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve coffees.
    """
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
    current_user: Any = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new coffee.
    """
    coffee = Coffee(
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
    current_user: Any = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update a coffee.
    """
    query = select(Coffee).where(Coffee.id == coffee_id)
    result = await db.execute(query)
    coffee = result.scalars().first()
    if not coffee:
        raise HTTPException(status_code=404, detail="Coffee not found")
        
    update_data = coffee_in.model_dump(exclude_unset=True) # Assuming Pydantic v2
    for field, value in update_data.items():
        setattr(coffee, field, value)
        
    db.add(coffee)
    await db.commit()
    await db.refresh(coffee)
    return coffee

@router.delete("/{coffee_id}", response_model=schemas.CoffeeResponse)
async def delete_coffee(
    *,
    db: AsyncSession = Depends(deps.get_db),
    coffee_id: int,
    current_user: Any = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Delete a coffee (or mark as inactive).
    """
    query = select(Coffee).where(Coffee.id == coffee_id)
    result = await db.execute(query)
    coffee = result.scalars().first()
    if not coffee:
        raise HTTPException(status_code=404, detail="Coffee not found")
        
    await db.delete(coffee)
    await db.commit()
    return coffee
