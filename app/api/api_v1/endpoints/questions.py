from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api import deps
from app.models.models import AuditQuestion, AuditCategory, User, UserRole
from app.schemas import schemas

router = APIRouter()


@router.get("", response_model=List[schemas.AuditQuestionResponse])
async def read_questions(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 200,
    category_id: Optional[int] = None,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Retrieve audit questions ordered by display_order."""

    query = (
        select(AuditQuestion)
        .options(selectinload(AuditQuestion.category).selectinload(AuditCategory.questions))
        .order_by(AuditQuestion.display_order)
    )
    if category_id:
        query = query.where(AuditQuestion.category_id == category_id)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/reorder")
async def reorder_questions(
    *,
    db: AsyncSession = Depends(deps.get_db),
    body: schemas.ReorderRequest,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Bulk-update display_order for questions. Admin only."""
    has_update_rights = current_user.rights and current_user.rights.questions_update
    if current_user.role != UserRole.ADMIN and not has_update_rights:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    result = await db.execute(select(AuditQuestion))
    questions = {q.id: q for q in result.scalars().all()}

    for item in body.items:
        if item.id in questions:
            questions[item.id].display_order = item.display_order

    await db.commit()
    return {"ok": True}


@router.get("/{question_id}", response_model=schemas.AuditQuestionResponse)
async def read_question(
    *,
    db: AsyncSession = Depends(deps.get_db),
    question_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    query = select(AuditQuestion).options(
        selectinload(AuditQuestion.category).selectinload(AuditCategory.questions)
    ).where(AuditQuestion.id == question_id)
    result = await db.execute(query)
    question = result.scalars().first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.post("", response_model=schemas.AuditQuestionResponse)
async def create_question(
    *,
    db: AsyncSession = Depends(deps.get_db),
    question_in: schemas.AuditQuestionCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    has_create_rights = current_user.rights and current_user.rights.questions_create
    if current_user.role != UserRole.ADMIN and not has_create_rights:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    category_query = select(AuditCategory).where(AuditCategory.id == question_in.category_id)
    category_result = await db.execute(category_query)
    if not category_result.scalars().first():
        raise HTTPException(status_code=404, detail="Category not found")

    # Auto-set display_order to max+1 in category if not provided
    count_result = await db.execute(
        select(AuditQuestion).where(AuditQuestion.category_id == question_in.category_id)
    )
    existing_count = len(count_result.scalars().all())

    question = AuditQuestion(
        text=question_in.text,
        weight=question_in.weight,
        category_id=question_in.category_id,
        correct_answer=question_in.correct_answer,
        na_score=question_in.na_score,
        display_order=question_in.display_order if question_in.display_order else existing_count,
    )
    db.add(question)
    await db.commit()
    await db.refresh(question)

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
    has_update_rights = current_user.rights and current_user.rights.questions_update
    if current_user.role != UserRole.ADMIN and not has_update_rights:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    query = select(AuditQuestion).where(AuditQuestion.id == question_id)
    result = await db.execute(query)
    question = result.scalars().first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    if question_in.category_id != question.category_id:
        cat_r = await db.execute(select(AuditCategory).where(AuditCategory.id == question_in.category_id))
        if not cat_r.scalars().first():
            raise HTTPException(status_code=404, detail="Category not found")

    question.text = question_in.text
    question.weight = question_in.weight
    question.category_id = question_in.category_id
    question.correct_answer = question_in.correct_answer
    question.na_score = question_in.na_score

    await db.commit()
    await db.refresh(question)

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
    has_delete_rights = current_user.rights and current_user.rights.questions_delete
    if current_user.role != UserRole.ADMIN and not has_delete_rights:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    query = select(AuditQuestion).where(AuditQuestion.id == question_id)
    result = await db.execute(query)
    question = result.scalars().first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    await db.delete(question)
    await db.commit()
    return {"ok": True}
