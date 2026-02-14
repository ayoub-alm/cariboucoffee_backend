from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api import deps
from app.models.models import Audit, AuditAnswer, AuditQuestion, AuditCategory, User, UserRole
from app.schemas import schemas

router = APIRouter()

@router.get("", response_model=List[schemas.AuditResponse])
async def read_audits(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve audits.
    - Admin: All audits
    - Auditor: Own audits
    - Viewer: Audits for their assigned coffee
    """
    try:
        query = select(Audit).options(
            selectinload(Audit.coffee),
            selectinload(Audit.auditor),
            selectinload(Audit.answers).selectinload(AuditAnswer.question).selectinload(AuditQuestion.category).selectinload(AuditCategory.questions)
        ).offset(skip).limit(limit)

        if current_user.role == UserRole.ADMIN:
            pass # No filter
        elif current_user.role == UserRole.AUDITOR:
            query = query.where(Audit.auditor_id == current_user.id)
        elif current_user.role == UserRole.VIEWER:
            if not current_user.coffee_id:
                return [] # Viewer with no coffee sees nothing
            query = query.where(Audit.coffee_id == current_user.coffee_id)
        
        result = await db.execute(query)
        audits = result.scalars().all()
        return audits
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("", response_model=schemas.AuditResponse)
async def create_audit(
    *,
    db: AsyncSession = Depends(deps.get_db),
    audit_in: schemas.AuditCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new audit.
    Only Admin and Auditor can create.
    """
    if current_user.role == UserRole.VIEWER:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # precise calculation of score logic can be added here
    # For now, just sum the values or something simple
    
    audit = Audit(
        coffee_id=audit_in.coffee_id,
        auditor_id=current_user.id,
        score=0.0, # Placeholder
        shift=audit_in.shift,
        staff_present=audit_in.staff_present,
        actions_correctives=audit_in.actions_correctives,
        training_needs=audit_in.training_needs,
        purchases=audit_in.purchases
    )
    db.add(audit)
    await db.commit()
    await db.refresh(audit)
    
    # Calculate weighted score
    total_weighted_score = 0
    total_max_weighted_score = 0
    
    for answer in audit_in.answers:
        # Fetch the question to get its weight
        question_result = await db.execute(
            select(AuditQuestion).where(AuditQuestion.id == answer.question_id)
        )
        question = question_result.scalars().first()
        
        if question:
            weight = question.weight
            max_value = 5 # Standard max points for calculation purposes, though logic changes
            
            # Logic Update per user feedback: Weight IS the score.
            score_for_question = 0
            max_score_possible = weight # The weight is the full point value
            
            user_choice = answer.choice.lower() if answer.choice else ""
            correct = question.correct_answer.lower() if question.correct_answer else "oui"
            
            if user_choice == correct:
                score_for_question = weight
            elif user_choice == 'n/a':
                score_for_question = question.na_score
            else:
                 score_for_question = 0
                 
            # Store points in value
            answer.value = score_for_question 
            
            total_weighted_score += score_for_question
            total_max_weighted_score += max_score_possible

        
        db_answer = AuditAnswer(
            audit_id=audit.id,
            question_id=answer.question_id,
            value=answer.value,
            choice=answer.choice,
            comment=answer.comment
        )
        db.add(db_answer)
    
    # Calculate percentage score
    if total_max_weighted_score > 0:
        audit.score = round((total_weighted_score / total_max_weighted_score) * 100, 2)
    else:
        audit.score = 0.0
    
    await db.commit()
    await db.refresh(audit)
    
    # Reload for response
    query = select(Audit).options(
        selectinload(Audit.coffee),
        selectinload(Audit.auditor),
        selectinload(Audit.answers).selectinload(AuditAnswer.question).selectinload(AuditQuestion.category).selectinload(AuditCategory.questions)
    ).where(Audit.id == audit.id)
    result = await db.execute(query)
    return result.scalars().first()

@router.get("/{audit_id}", response_model=schemas.AuditResponse)
async def read_audit(
    *,
    db: AsyncSession = Depends(deps.get_db),
    audit_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get audit by ID.
    """
    query = select(Audit).options(
        selectinload(Audit.coffee),
        selectinload(Audit.auditor),
        selectinload(Audit.answers).selectinload(AuditAnswer.question).selectinload(AuditQuestion.category).selectinload(AuditCategory.questions)
    ).where(Audit.id == audit_id)
    
    result = await db.execute(query)
    audit = result.scalars().first()
    
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    # Authorization check
    if current_user.role == UserRole.ADMIN:
        pass  # Admin can see all
    elif current_user.role == UserRole.AUDITOR:
        if audit.auditor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this audit")
    elif current_user.role == UserRole.VIEWER:
        if audit.coffee_id != current_user.coffee_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this audit")
    
    return audit


@router.put("/{id}", response_model=schemas.AuditResponse)
async def update_audit(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int,
    audit_in: schemas.AuditUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update an audit.
    Admin or Auditor (own audit).
    """
    query = select(Audit).options(
        selectinload(Audit.coffee),
        selectinload(Audit.auditor),
        selectinload(Audit.answers)
    ).where(Audit.id == id)
    result = await db.execute(query)
    audit = result.scalars().first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
        
    # Check permissions
    if current_user.role == UserRole.ADMIN:
        pass
    elif current_user.role == UserRole.AUDITOR:
        if audit.auditor_id != current_user.id:
             raise HTTPException(status_code=403, detail="Not enough permissions")
    else:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Update basic fields
    if audit_in.coffee_id is not None:
        audit.coffee_id = audit_in.coffee_id
    if audit_in.shift is not None:
        audit.shift = audit_in.shift
    if audit_in.staff_present is not None:
        audit.staff_present = audit_in.staff_present
    if audit_in.actions_correctives is not None:
        audit.actions_correctives = audit_in.actions_correctives
    if audit_in.training_needs is not None:
        audit.training_needs = audit_in.training_needs
    if audit_in.purchases is not None:
        audit.purchases = audit_in.purchases

    # If answers provided, replace logic
    if audit_in.answers is not None:
        # Delete old answers
        # Simple approach: delete all DB answers for this audit
        # In async sqlalchemy this is delete(AuditAnswer).where(AuditAnswer.audit_id == id)
        # But we loaded them via selectinload, so usage of relationship might interfere or be updated?
        # Let's try explicit delete query
        from sqlalchemy import delete
        await db.execute(delete(AuditAnswer).where(AuditAnswer.audit_id == id))
        
        total_weighted_score = 0
        total_max_weighted_score = 0

        for answer in audit_in.answers:
            # Fetch the question to get its weight and scoring rules
            question_result = await db.execute(
                select(AuditQuestion).where(AuditQuestion.id == answer.question_id)
            )
            question = question_result.scalars().first()
            
            score_for_question = 0
            if question:
                weight = question.weight
                max_score_possible = weight # Weight IS the points
                
                user_choice = answer.choice.lower() if answer.choice else ""
                correct = question.correct_answer.lower() if question.correct_answer else "oui"
                
                if user_choice == correct:
                     score_for_question = weight
                elif user_choice == 'n/a':
                     score_for_question = question.na_score
                     # If N/A gives points, does it count towards max?
                     # Usually N/A means "Not Applicable" -> remove from max.
                     # But user said "N/A defined point".
                     # If I answer N/A and get 5 points (out of 10?), that's weird.
                     # If I answer N/A and get 'na_score' points, maybe max is also adjusted?
                     # Let's assume for now: Max is still 'weight' (the question's value).
                     # And N/A gives you 'na_score' points out of 'weight'.
                     # If na_score > weight, that would be bonus.
                     pass 
                else:
                     score_for_question = 0
                
                # Store the actual points awarded in value
                answer.value = score_for_question
                
                total_weighted_score += score_for_question
                # If answer is N/A, usually we exclude from denominator if it's truly "Not Applicable".
                # But if N/A has specific points, it implies it's a valid scored answer.
                # However, if N/A points is 0, and we keep it in max_score, it penalizes.
                # If user sets N/A points to 0, maybe they want it excluded?
                # "make the use able to chose the corret user cause some times non anwsor can be the right question"
                # "N/A difned point in the creation"
                # Let's keep it simple: It counts towards max score implies it's a scored field.
                total_max_weighted_score += max_score_possible


            db_answer = AuditAnswer(
                audit_id=audit.id,
                question_id=answer.question_id,
                value=answer.value,
                choice=answer.choice,
                comment=answer.comment
            )
            db.add(db_answer)
        
        # Calculate percentage score
        if total_max_weighted_score > 0:
            audit.score = round((total_weighted_score / total_max_weighted_score) * 100, 2)
        else:
            audit.score = 0.0

    
    await db.commit()
    await db.refresh(audit)
    
    # Re-fetch for response with eager loading to be safe
    result = await db.execute(query)
    return result.scalars().first()

@router.delete("/{id}", response_model=schemas.AuditResponse)
async def delete_audit(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Delete an audit.
    Only Admin can delete? Or Auditor can delete their own?
    Let's say Admin only for deletion to be safe, or Auditor their own.
    """
    query = select(Audit).where(Audit.id == id)
    result = await db.execute(query)
    audit = result.scalars().first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
        
    if current_user.role == UserRole.ADMIN:
        pass
    elif current_user.role == UserRole.AUDITOR:
        if audit.auditor_id != current_user.id:
             raise HTTPException(status_code=403, detail="Not enough permissions")
    else:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    await db.delete(audit)
    await db.commit()
    return audit
