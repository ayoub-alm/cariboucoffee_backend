import json
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from fastapi.responses import Response

from app.api import deps
from app.models.models import Audit, AuditAnswer, AuditQuestion, AuditCategory, AuditStatus, User, UserRole
from app.schemas import schemas
from app.utils.image_utils import save_base64_image
from app.utils.pdf_generator import generate_audit_pdf


def _save_photo_list(photo_data_list: list[str] | None) -> str | None:
    """Save a list of base64 images and return a JSON array of URLs.
    Correctly retains existing image HTTP URLs without breaking."""
    if not photo_data_list:
        return None
    urls = []
    for item in photo_data_list:
        if item.startswith("data:"):
            url = save_base64_image(item)
            if url:
                urls.append(url)
        else:
            # Keep existing server-side photos
            if "/static/" in item:
                relative = "/static/" + item.split("/static/", 1)[1]
            else:
                relative = item
            urls.append(relative)
            
    return json.dumps(urls) if urls else None


def _merge_photo_urls(
    existing_photo_urls: list[str] | None,
    new_photo_data: list[str] | None,
) -> str | None:
    """Merge previously saved photo URLs with newly uploaded base64 images.
    
    - existing_photo_urls: full URLs the frontend wants to keep (e.g. http://host/static/uploads/x.jpg)
    - new_photo_data: base64 images to save to disk
    Returns a JSON-encoded list of relative server paths.
    """
    all_urls: list[str] = []

    # Keep existing server-side photos (strip base URL to get relative path)
    if existing_photo_urls:
        for url in existing_photo_urls:
            # Strip any base URL prefix to get the relative path like /static/uploads/x.jpg
            if "/static/" in url:
                relative = "/static/" + url.split("/static/", 1)[1]
            else:
                relative = url
            all_urls.append(relative)

    # Save new base64 photos and add their URLs
    if new_photo_data:
        for b64 in new_photo_data:
            url = save_base64_image(b64)
            if url:
                all_urls.append(url)

    return json.dumps(all_urls) if all_urls else None

router = APIRouter()

@router.get("", response_model=List[schemas.AuditResponse])
async def read_audits(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 10000,
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

        has_read_rights = current_user.rights and current_user.rights.audits_read
        if current_user.role in (UserRole.ADMIN, UserRole.BOSS) or has_read_rights:
            # Full access if ADMIN/BOSS or explicit audits_read permission
            pass
        elif current_user.role == UserRole.AUDITOR:
            # Auditor sees their own
            query = query.where(Audit.auditor_id == current_user.id)
        elif current_user.role == UserRole.MANAGER:
            managed_ids = [c.id for c in current_user.managed_coffees] if current_user.managed_coffees else []
            if not managed_ids:
                return []
            query = query.where(Audit.coffee_id.in_(managed_ids))
        elif current_user.role == UserRole.VIEWER:
            if not current_user.coffee_id:
                return []
            query = query.where(Audit.coffee_id == current_user.coffee_id)
        else:
            # Fallback for roles like MANAGER without explicit rights (handled by business logic above already)
            # but if something else hits here, return empty
            return []
        
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
    try:
        can_create = current_user.role in (UserRole.ADMIN, UserRole.AUDITOR)
        if not can_create and current_user.rights and current_user.rights.audits_create:
            can_create = True
            
        if not can_create:
            raise HTTPException(status_code=403, detail="Not enough permissions")

        photo_url = _merge_photo_urls(audit_in.existing_photo_urls, audit_in.photo_data)

        audit = Audit(
            coffee_id=audit_in.coffee_id,
            auditor_id=current_user.id,
            date=audit_in.date,
            score=0.0,
            status=audit_in.status or AuditStatus.IN_PROGRESS,
            shift=audit_in.shift,
            staff_present=audit_in.staff_present,
            actions_correctives=audit_in.actions_correctives,
            training_needs=audit_in.training_needs,
            purchases=audit_in.purchases,
            photo_url=photo_url
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
            
            if not question:
                print(f"Skipping invalid question_id: {answer.question_id}")
                continue

            if question:
                weight = question.weight or 1
                
                user_choice = answer.choice.lower() if answer.choice else ""
                correct_ans = question.correct_answer.lower() if question.correct_answer else "oui"
                
                calculated_value = 0
                max_score_possible = weight 

                if user_choice == 'n/a':
                     # New Logic: N/A skips the question entirely from scoring
                     # We store 0 for value, and do NOT add to totals
                     calculated_value = 0
                else:
                    # Normal scoring
                    if user_choice == correct_ans:
                        calculated_value = weight
                    else:
                        calculated_value = 0
                    
                    total_weighted_score += calculated_value
                    total_max_weighted_score += max_score_possible
            else:
                # Should not happen due to 'if not question: continue' check, but safe default
                calculated_value = 0

            answer_photo_url = _save_photo_list(answer.photo_data)

            db_answer = AuditAnswer(
                audit_id=audit.id,
                question_id=answer.question_id,
                value=calculated_value,
                choice=answer.choice,
                comment=answer.comment,
                photo_url=answer_photo_url
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
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creating audit: {str(e)}")

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
    
    has_read_rights = current_user.rights and current_user.rights.audits_read
    if current_user.role in (UserRole.ADMIN, UserRole.BOSS) or has_read_rights:
        pass
    elif current_user.role == UserRole.AUDITOR:
        if audit.auditor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this audit")
    elif current_user.role == UserRole.MANAGER:
        managed_ids = [c.id for c in current_user.managed_coffees] if current_user.managed_coffees else []
        if audit.coffee_id not in managed_ids:
            raise HTTPException(status_code=403, detail="Not authorized to view this audit")
    elif current_user.role == UserRole.VIEWER:
        if audit.coffee_id != current_user.coffee_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this audit")
    else:
        raise HTTPException(status_code=403, detail="Not authorized to view this audit")
    
    return audit

@router.get("/{audit_id}/pdf")
async def download_audit_pdf(
    *,
    db: AsyncSession = Depends(deps.get_db),
    audit_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Response:
    """
    Get audit report as PDF.
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
        
    if current_user.role in (UserRole.ADMIN, UserRole.BOSS):
        pass
    elif current_user.role == UserRole.AUDITOR:
        if audit.auditor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this audit")
    elif current_user.role == UserRole.MANAGER:
        managed_ids = [c.id for c in current_user.managed_coffees] if current_user.managed_coffees else []
        if audit.coffee_id not in managed_ids:
            raise HTTPException(status_code=403, detail="Not authorized to view this audit")
    elif current_user.role == UserRole.VIEWER:
        if audit.coffee_id != current_user.coffee_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this audit")

    try:
        pdf_bytes = generate_audit_pdf(audit)
        
        filename = f"audit_{audit.coffee.name}_{audit.created_at.strftime('%Y%m%d') if audit.created_at else 'report'}.pdf"
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        return Response(content=bytes(pdf_bytes), media_type="application/pdf", headers=headers)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")

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
    - Admin can update any audit (including completed ones).
    - Auditor can only update their own IN_PROGRESS audits.
    """
    query = select(Audit).options(
        selectinload(Audit.coffee),
        selectinload(Audit.auditor),
        selectinload(Audit.answers).selectinload(AuditAnswer.question).selectinload(AuditQuestion.category).selectinload(AuditCategory.questions)
    ).where(Audit.id == id)
    result = await db.execute(query)
    audit = result.scalars().first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
        
    has_update_rights = current_user.rights and current_user.rights.audits_update
    if current_user.role == UserRole.ADMIN or has_update_rights:
        pass
    elif current_user.role == UserRole.AUDITOR:
        if audit.auditor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        if audit.status == AuditStatus.COMPLETED:
            raise HTTPException(status_code=403, detail="Completed audits cannot be modified")
    else:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if audit_in.status is not None:
        audit.status = audit_in.status
    if audit_in.coffee_id is not None:
        audit.coffee_id = audit_in.coffee_id
    if audit_in.date is not None:
        audit.date = audit_in.date
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
    # Merge existing photo URLs with any new uploads
    if audit_in.photo_data is not None or audit_in.existing_photo_urls is not None:
        merged = _merge_photo_urls(audit_in.existing_photo_urls, audit_in.photo_data)
        audit.photo_url = merged

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
            
            if not question:
                print(f"Skipping invalid question_id in update: {answer.question_id}")
                continue

            if question:
                weight = question.weight or 1
                max_score_possible = weight 
                
                user_choice = answer.choice.lower() if answer.choice else ""
                correct_ans = question.correct_answer.lower() if question.correct_answer else "oui"

                calculated_value = 0

                if user_choice == 'n/a':
                     # New Logic: N/A skips scoring
                     calculated_value = 0
                else:
                    if user_choice == correct_ans:
                         calculated_value = weight
                    else:
                         calculated_value = 0
                    
                    total_weighted_score += calculated_value
                    total_max_weighted_score += max_score_possible
            else:
                 calculated_value = 0


            db_answer = AuditAnswer(
                audit_id=audit.id,
                question_id=answer.question_id,
                value=calculated_value,
                choice=answer.choice,
                comment=answer.comment,
                photo_url=_save_photo_list(answer.photo_data)
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
    Delete an audit. Only Admin can delete.
    """
    has_delete_rights = current_user.rights and current_user.rights.audits_delete
    if current_user.role != UserRole.ADMIN and not has_delete_rights:
        raise HTTPException(status_code=403, detail="Not enough permissions to delete audits")

    query = select(Audit).where(Audit.id == id)
    result = await db.execute(query)
    audit = result.scalars().first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    await db.delete(audit)
    await db.commit()
    return audit

@router.post("/bulk-delete")
async def bulk_delete_audits(
    *,
    db: AsyncSession = Depends(deps.get_db),
    body: schemas.BulkDelete,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Bulk delete audits. Only Admin can delete.
    """
    has_delete_rights = current_user.rights and current_user.rights.audits_delete
    if current_user.role != UserRole.ADMIN and not has_delete_rights:
        raise HTTPException(status_code=403, detail="Only administrators or authorized users can delete audits")


    if not body.ids:
        return {"message": "No ids provided"}

    from sqlalchemy import delete
    query = delete(Audit).where(Audit.id.in_(body.ids))
    await db.execute(query)
    await db.commit()
    
    return {"message": f"Successfully deleted {len(body.ids)} audits"}
