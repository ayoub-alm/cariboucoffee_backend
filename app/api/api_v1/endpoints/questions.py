from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api import deps
from app.models.models import AuditQuestion, AuditCategory, User, UserRole
from app.schemas import schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.AuditQuestionResponse])
async def read_questions(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 200,
    category_id: int = None,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve audit questions.
    Optionally filter by category_id.
    """
    query = select(AuditQuestion).options(
        selectinload(AuditQuestion.category).selectinload(AuditCategory.questions)
    )
    
    if category_id:
        query = query.where(AuditQuestion.category_id == category_id)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    questions = result.scalars().all()
    return questions

@router.get("/{question_id}", response_model=schemas.AuditQuestionResponse)
async def read_question(
    *,
    db: AsyncSession = Depends(deps.get_db),
    question_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get question by ID.
    """
    query = select(AuditQuestion).options(
        selectinload(AuditQuestion.category).selectinload(AuditCategory.questions)
    ).where(AuditQuestion.id == question_id)
    result = await db.execute(query)
    question = result.scalars().first()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return question

@router.post("/", response_model=schemas.AuditQuestionResponse)
async def create_question(
    *,
    db: AsyncSession = Depends(deps.get_db),
    question_in: schemas.AuditQuestionCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new audit question.
    Only Admin can create.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Verify category exists
    category_query = select(AuditCategory).where(AuditCategory.id == question_in.category_id)
    category_result = await db.execute(category_query)
    category = category_result.scalars().first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    question = AuditQuestion(
        text=question_in.text,
        weight=question_in.weight,
        category_id=question_in.category_id,
        correct_answer=question_in.correct_answer,
        na_score=question_in.na_score

    )
    db.add(question)
    await db.commit()
    await db.refresh(question)
    
    # Reload with category
    query = select(AuditQuestion).options(
        selectinload(AuditQuestion.category).selectinload(AuditCategory.questions)
    ).where(AuditQuestion.id == question.id)
    result = await db.execute(query)
    return result.scalars().first()

@router.put("/{question_id}", response_model=schemas.AuditQuestionResponse)
async def update_question(
    *,
    db: AsyncSession = Depends(deps.get_db),
    question_id: int,
    question_in: schemas.AuditQuestionCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update audit question.
    Only Admin can update.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    query = select(AuditQuestion).where(AuditQuestion.id == question_id)
    result = await db.execute(query)
    question = result.scalars().first()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Verify category exists if changing
    if question_in.category_id != question.category_id:
        category_query = select(AuditCategory).where(AuditCategory.id == question_in.category_id)
        category_result = await db.execute(category_query)
        category = category_result.scalars().first()
        
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    
    question.text = question_in.text
    question.weight = question_in.weight
    question.category_id = question_in.category_id
    question.correct_answer = question_in.correct_answer
    question.na_score = question_in.na_score

    
    await db.commit()
    await db.refresh(question)
    
    # Reload with category
    query = select(AuditQuestion).options(
        selectinload(AuditQuestion.category).selectinload(AuditCategory.questions)
    ).where(AuditQuestion.id == question.id)
    result = await db.execute(query)
    return result.scalars().first()

@router.delete("/{question_id}")
async def delete_question(
    *,
    db: AsyncSession = Depends(deps.get_db),
    question_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Delete audit question.
    Only Admin can delete.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    query = select(AuditQuestion).where(AuditQuestion.id == question_id)
    result = await db.execute(query)
    question = result.scalars().first()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    await db.delete(question)
    await db.commit()
    return {"ok": True}
