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

@router.get("", response_model=schemas.AuditListResponse)
async def read_audits(
    db: AsyncSession = Depends(deps.get_db),
    page: int = 1,
    size: int = 25,
    search: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    coffee_id: int | None = None,
    coffee_shop: str | None = None,
    auditor_id: int | None = None,
    auditor_name: str | None = None,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve audits with server-side pagination.
    - Admin/Boss: All audits
    - Auditor: Own audits
    - Manager: Audits for their managed coffees
    - Viewer: Audits for their assigned coffee
    """
    try:
        import math
        from datetime import datetime
        from sqlalchemy import func, and_, or_
        from app.models.models import Coffee, User as DBUser

        empty_response = {
            "items": [], "total": 0, "page": page,
            "size": size, "pages": 0, "average_score": 0.0
        }

        # ── 1. Access-control conditions ──────────────────────────────────
        base_conditions = []
        has_read_rights = current_user.rights and current_user.rights.audits_read

        if current_user.role in (UserRole.ADMIN, UserRole.BOSS):
            pass
        elif current_user.role == UserRole.AUDITOR:
            base_conditions.append(Audit.auditor_id == current_user.id)
        elif has_read_rights:
            pass
        elif current_user.role == UserRole.MANAGER:
            managed_ids = [c.id for c in current_user.managed_coffees] if current_user.managed_coffees else []
            if not managed_ids:
                return empty_response
            base_conditions.append(Audit.coffee_id.in_(managed_ids))
        elif current_user.role == UserRole.VIEWER:
            if not current_user.coffee_id:
                return empty_response
            base_conditions.append(Audit.coffee_id == current_user.coffee_id)
        else:
            return empty_response

        # ── 2. Date / scalar filter conditions ────────────────────────────
        if start_date:
            try:
                dt = datetime.fromisoformat(start_date.replace("Z", "+00:00")).date()
                base_conditions.append(Audit.date >= dt)
            except ValueError:
                try:
                    dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                    base_conditions.append(Audit.date >= dt)
                except ValueError:
                    pass

        if end_date:
            try:
                dt = datetime.fromisoformat(end_date.replace("Z", "+00:00")).date()
                base_conditions.append(Audit.date <= dt)
            except ValueError:
                try:
                    dt = datetime.strptime(end_date, "%Y-%m-%d").date()
                    base_conditions.append(Audit.date <= dt)
                except ValueError:
                    pass

        if coffee_id:
            base_conditions.append(Audit.coffee_id == coffee_id)

        if auditor_id:
            base_conditions.append(Audit.auditor_id == auditor_id)

        # ── 3. Determine which JOINs are required ─────────────────────────
        need_coffee_join  = bool(coffee_shop or search)
        need_auditor_join = bool(auditor_name or search)

        def _build(base_select):
            """Apply joins, conditions, and text-filters to any SELECT."""
            q = base_select
            if need_coffee_join:
                q = q.join(Coffee, Audit.coffee_id == Coffee.id)
            if need_auditor_join:
                q = q.join(DBUser, Audit.auditor_id == DBUser.id)
            if base_conditions:
                q = q.where(and_(*base_conditions))
            if coffee_shop:
                q = q.where(Coffee.name == coffee_shop)
            if auditor_name:
                q = q.where(
                    (DBUser.full_name == auditor_name) | (DBUser.email == auditor_name)
                )
            if search:
                s = f"%{search.lower()}%"
                q = q.where(
                    or_(
                        func.lower(Coffee.name).like(s),
                        func.lower(func.coalesce(DBUser.full_name, "")).like(s),
                        func.lower(DBUser.email).like(s),
                    )
                )
            return q

        # ── 4. COUNT + AVG query ───────────────────────────────────────────
        count_q = _build(
            select(func.count(Audit.id), func.coalesce(func.avg(Audit.score), 0.0))
        )
        count_result = await db.execute(count_q)
        total, avg_score = count_result.one()
        total     = int(total or 0)
        avg_score = round(float(avg_score or 0), 2)
        pages     = math.ceil(total / size) if size > 0 and total > 0 else 0

        # ── 5. Paginated data query ────────────────────────────────────────
        data_q = _build(
            select(Audit).options(
                selectinload(Audit.coffee),
                selectinload(Audit.auditor),
                selectinload(Audit.answers)
                    .selectinload(AuditAnswer.question)
                    .selectinload(AuditQuestion.category)
                    .selectinload(AuditCategory.questions)
            )
        )
        offset = (max(page, 1) - 1) * size
        data_q = data_q.order_by(Audit.date.desc(), Audit.created_at.desc()).offset(offset).limit(size)

        result = await db.execute(data_q)
        audits = result.scalars().all()

        return {
            "items":         audits,
            "total":         total,
            "page":          page,
            "size":          size,
            "pages":         pages,
            "average_score": avg_score,
        }
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
            conclusion=audit_in.conclusion,
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

@router.get("/export-excel")
async def export_audits_excel(
    db: AsyncSession = Depends(deps.get_db),
    search: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    coffee_id: int | None = None,
    coffee_shop: str | None = None,
    auditor_id: int | None = None,
    auditor_name: str | None = None,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Export audits in Excel format.
    """
    try:
        from datetime import datetime
        from sqlalchemy import func, and_, or_
        from app.models.models import Coffee, User as DBUser, ConformityThreshold, AuditStatus
        
        # ── 1. Access-control conditions ──────────────────────────────────
        base_conditions = []
        has_read_rights = current_user.rights and current_user.rights.audits_read

        if current_user.role in (UserRole.ADMIN, UserRole.BOSS):
            pass
        elif current_user.role == UserRole.AUDITOR:
            base_conditions.append(Audit.auditor_id == current_user.id)
        elif has_read_rights:
            pass
        elif current_user.role == UserRole.MANAGER:
            managed_ids = [c.id for c in current_user.managed_coffees] if current_user.managed_coffees else []
            if not managed_ids:
                raise HTTPException(status_code=400, detail="Vous ne gérez aucun café.")
            base_conditions.append(Audit.coffee_id.in_(managed_ids))
        elif current_user.role == UserRole.VIEWER:
            if not current_user.coffee_id:
                raise HTTPException(status_code=400, detail="Aucun café assigné.")
            base_conditions.append(Audit.coffee_id == current_user.coffee_id)
        else:
            raise HTTPException(status_code=403, detail="Accès non autorisé.")

        # ── 2. Date / scalar filter conditions ────────────────────────────
        if start_date:
            try:
                dt = datetime.fromisoformat(start_date.replace("Z", "+00:00")).date()
                base_conditions.append(Audit.date >= dt)
            except ValueError:
                try:
                    dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                    base_conditions.append(Audit.date >= dt)
                except ValueError:
                    pass

        if end_date:
            try:
                dt = datetime.fromisoformat(end_date.replace("Z", "+00:00")).date()
                base_conditions.append(Audit.date <= dt)
            except ValueError:
                try:
                    dt = datetime.strptime(end_date, "%Y-%m-%d").date()
                    base_conditions.append(Audit.date <= dt)
                except ValueError:
                    pass

        if coffee_id:
            base_conditions.append(Audit.coffee_id == coffee_id)

        if auditor_id:
            base_conditions.append(Audit.auditor_id == auditor_id)

        need_coffee_join  = bool(coffee_shop or search)
        need_auditor_join = bool(auditor_name or search)

        def _build(base_select):
            q = base_select
            if need_coffee_join:
                q = q.join(Coffee, Audit.coffee_id == Coffee.id)
            if need_auditor_join:
                q = q.join(DBUser, Audit.auditor_id == DBUser.id)
            if base_conditions:
                q = q.where(and_(*base_conditions))
            if coffee_shop:
                q = q.where(Coffee.name == coffee_shop)
            if auditor_name:
                q = q.where(
                    (DBUser.full_name == auditor_name) | (DBUser.email == auditor_name)
                )
            if search:
                s = f"%{search.lower()}%"
                q = q.where(
                    or_(
                        func.lower(Coffee.name).like(s),
                        func.lower(func.coalesce(DBUser.full_name, "")).like(s),
                        func.lower(DBUser.email).like(s),
                    )
                )
            return q

        # ── 3. Query all filtered audits (non-paginated) ──────────────────
        data_q = _build(
            select(Audit).options(
                selectinload(Audit.coffee),
                selectinload(Audit.auditor)
            )
        )
        data_q = data_q.order_by(Audit.date.desc(), Audit.created_at.desc())
        result = await db.execute(data_q)
        audits = result.scalars().all()

        # ── 4. Fetch thresholds ───────────────────────────────────────────
        t_result = await db.execute(select(ConformityThreshold).limit(1))
        thresholds = t_result.scalars().first()
        conforme_min = thresholds.conforme_min if thresholds and thresholds.conforme_min is not None else 80.0
        partiel_min = thresholds.partiel_min if thresholds and thresholds.partiel_min is not None else 70.0

        def get_audit_status(score: float) -> str:
            if score >= conforme_min:
                return "Conforme"
            if score >= partiel_min:
                return "Partiel"
            return "Non conforme"

        def get_score_style(score: float) -> str:
            if score >= conforme_min:
                return "GoodStyle"
            if score >= partiel_min:
                return "WarningStyle"
            return "BadStyle"

        def escape_xml(val: Any) -> str:
            if val is None:
                return ""
            s = str(val)
            return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;").replace("'", "&apos;")

        # ── 5. Generate Excel Rows ────────────────────────────────────────
        rows_xml = []
        for audit in audits:
            status_label = "En cours" if audit.status == AuditStatus.IN_PROGRESS else get_audit_status(audit.score)
            score_style = "NumberStyle" if audit.status == AuditStatus.IN_PROGRESS else get_score_style(audit.score)
            auditor_name = audit.auditor.full_name if audit.auditor else "N/A"
            coffee_name = audit.coffee.name if audit.coffee else "N/A"
            date_str = audit.date.strftime("%d/%m/%Y %H:%M") if audit.date else ""
            conclusion = audit.conclusion or audit.actions_correctives or ""
            workflow_status = audit.status.value if hasattr(audit.status, "value") else audit.status
            
            rows_xml.append(f"""
   <Row ss:Height="20">
    <Cell><Data ss:Type="Number">{audit.id}</Data></Cell>
    <Cell><Data ss:Type="String">{escape_xml(coffee_name)}</Data></Cell>
    <Cell><Data ss:Type="String">{escape_xml(auditor_name)}</Data></Cell>
    <Cell><Data ss:Type="String">{escape_xml(date_str)}</Data></Cell>
    <Cell ss:StyleID="{score_style}"><Data ss:Type="Number">{round(audit.score) if audit.score is not None else 0}</Data></Cell>
    <Cell><Data ss:Type="String">{escape_xml(status_label)}</Data></Cell>
    <Cell><Data ss:Type="String">{escape_xml(conclusion)}</Data></Cell>
    <Cell><Data ss:Type="String">{escape_xml(workflow_status)}</Data></Cell>
   </Row>""")

        if start_date and end_date:
            period_text = f"Du {start_date} au {end_date}"
        elif start_date:
            period_text = f"Depuis le {start_date}"
        elif end_date:
            period_text = f"Jusqu'au {end_date}"
        else:
            period_text = "Toutes les dates disponibles"

        export_date_text = datetime.now().strftime("%d/%m/%Y %H:%M")
        generated_by_text = current_user.full_name if current_user.full_name else current_user.email

        # Compile Workbook XML
        workbook_xml = f"""<?xml version="1.0"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:x="urn:schemas-microsoft-com:office:excel"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:html="http://www.w3.org/TR/REC-html40">
 <Styles>
  <Style ss:ID="Default" ss:Name="Normal">
   <Alignment ss:Vertical="Bottom"/>
   <Borders/>
   <Font ss:FontName="Calibri" x:CharSet="1" x:Family="Swiss" ss:Size="11" ss:Color="#000000"/>
   <Interior/>
   <NumberFormat/>
   <Protection/>
  </Style>
  <Style ss:ID="Header">
   <Font ss:FontName="Calibri" ss:Size="11" ss:Bold="1" ss:Color="#FFFFFF"/>
   <Interior ss:Color="#005B70" ss:Pattern="Solid"/>
   <Alignment ss:Horizontal="Center" ss:Vertical="Center"/>
  </Style>
  <Style ss:ID="SubHeader">
   <Font ss:FontName="Calibri" ss:Size="11" ss:Bold="1" ss:Color="#FFFFFF"/>
   <Interior ss:Color="#2E7D90" ss:Pattern="Solid"/>
   <Alignment ss:Horizontal="Left" ss:Vertical="Center"/>
  </Style>
  <Style ss:ID="BoldText">
   <Font ss:FontName="Calibri" ss:Size="11" ss:Bold="1"/>
  </Style>
  <Style ss:ID="NumberStyle">
   <Alignment ss:Horizontal="Right" ss:Vertical="Center"/>
   <NumberFormat ss:Format="0"/>
  </Style>
  <Style ss:ID="GoodStyle">
   <Font ss:FontName="Calibri" ss:Size="11" ss:Color="#276A3C" ss:Bold="1"/>
   <Interior ss:Color="#E2EFDA" ss:Pattern="Solid"/>
   <Alignment ss:Horizontal="Right" ss:Vertical="Center"/>
   <NumberFormat ss:Format="0"/>
  </Style>
  <Style ss:ID="WarningStyle">
   <Font ss:FontName="Calibri" ss:Size="11" ss:Color="#7A5600" ss:Bold="1"/>
   <Interior ss:Color="#FEF7E0" ss:Pattern="Solid"/>
   <Alignment ss:Horizontal="Right" ss:Vertical="Center"/>
   <NumberFormat ss:Format="0"/>
  </Style>
  <Style ss:ID="BadStyle">
   <Font ss:FontName="Calibri" ss:Size="11" ss:Color="#A51D24" ss:Bold="1"/>
   <Interior ss:Color="#FCE8E6" ss:Pattern="Solid"/>
   <Alignment ss:Horizontal="Right" ss:Vertical="Center"/>
   <NumberFormat ss:Format="0"/>
  </Style>
 </Styles>
 <Worksheet ss:Name="Registre des Audits">
  <Table>
   <Row ss:Height="22"><Cell ss:MergeAcross="7" ss:StyleID="SubHeader"><Data ss:Type="String">Registre des Audits</Data></Cell></Row>
   <Row ss:Height="18">
    <Cell ss:StyleID="BoldText"><Data ss:Type="String">Période :</Data></Cell>
    <Cell ss:MergeAcross="6"><Data ss:Type="String">{escape_xml(period_text)}</Data></Cell>
   </Row>
   <Row ss:Height="18">
    <Cell ss:StyleID="BoldText"><Data ss:Type="String">Date d'export :</Data></Cell>
    <Cell ss:MergeAcross="6"><Data ss:Type="String">{escape_xml(export_date_text)}</Data></Cell>
   </Row>
   <Row ss:Height="18">
    <Cell ss:StyleID="BoldText"><Data ss:Type="String">Généré par :</Data></Cell>
    <Cell ss:MergeAcross="6"><Data ss:Type="String">{escape_xml(generated_by_text)}</Data></Cell>
   </Row>
   <Row ss:Height="15"></Row> <!-- Spacer -->
   <Row ss:Height="20">
    <Cell ss:StyleID="Header"><Data ss:Type="String">ID</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Café</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Auditeur</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Date</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Score (%)</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Statut</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Conclusion</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">État Workflow</Data></Cell>
   </Row>{"".join(rows_xml)}
  </Table>
 </Worksheet>
</Workbook>"""

        date_str = datetime.now().strftime("%Y-%m-%d")
        return Response(
            content=workbook_xml,
            media_type="application/vnd.ms-excel",
            headers={
                "Content-Disposition": f"attachment; filename=audits_export_{date_str}.xls",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

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
        
    is_owner = audit.auditor_id == current_user.id
    has_update_rights = current_user.rights and current_user.rights.audits_update
    
    # Permission Logic:
    # 1. Admin or user with explicit update rights can update any audit
    # 2. The creator (owner) can always update their own audit
    if current_user.role == UserRole.ADMIN or has_update_rights or is_owner:
        pass
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
    if audit_in.conclusion is not None:
        audit.conclusion = audit_in.conclusion
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

@router.delete("/{id}")
async def delete_audit(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Delete an audit.
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
    return {"message": "Audit deleted successfully", "id": id}


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
