from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import datetime

from app.api import deps
from app.models.models import DailyTimeRecord, ScheduleThreshold, UserRole, User, Coffee
from app.schemas import schemas

router = APIRouter()


def _time_to_minutes(t: str) -> int:
    """Convert 'HH:MM' string to total minutes."""
    try:
        h, m = map(int, t.split(":"))
        return h * 60 + m
    except Exception:
        return 0


def _compute_score(log: DailyTimeRecord, coffee: Optional[Coffee]) -> float:
    """Compute score as (real_range / config_range) * 100, capped at 100."""
    if not coffee:
        return 100.0
    if not coffee.opening_time or not coffee.closing_time:
        return 100.0
    if not log.opening_time or not log.closing_time:
        return 0.0

    config_start = _time_to_minutes(coffee.opening_time)
    config_end   = _time_to_minutes(coffee.closing_time)
    config_range = config_end - config_start

    real_start = _time_to_minutes(log.opening_time)
    real_end   = _time_to_minutes(log.closing_time)
    real_range = real_end - real_start

    if config_range <= 0:
        return 100.0

    percentage = (real_range / config_range) * 100.0
    return min(round(percentage, 2), 100.0)


def _compute_status(score: float, thr: Optional[ScheduleThreshold]) -> str:
    green_min  = thr.green_min  if thr else 100.0
    orange_min = thr.orange_min if thr else 90.0
    if score >= green_min:
        return "green"
    if score >= orange_min:
        return "orange"
    return "red"


@router.get("", response_model=schemas.DailyLogListResponse)
async def read_daily_logs(
    db: AsyncSession = Depends(deps.get_db),
    page: int = 1,
    size: int = 25,
    coffee_id: Optional[int] = None,
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Retrieve daily logs with server-side pagination and pre-computed KPI stats."""
    import math

    if current_user.role not in [UserRole.ADMIN, UserRole.BOSS, UserRole.CONTROLLER, UserRole.MANAGER]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    # Load schedule thresholds once
    thr_result = await db.execute(select(ScheduleThreshold).limit(1))
    thr = thr_result.scalars().first()

    # Load all coffees into a dict for fast lookup
    coffees_result = await db.execute(select(Coffee))
    coffees = {c.id: c for c in coffees_result.scalars().all()}

    # Build base query with filters applied
    query = select(DailyTimeRecord)
    
    if current_user.role == UserRole.MANAGER:
        managed_ids = [c.id for c in current_user.managed_coffees] if current_user.managed_coffees else []
        if coffee_id is not None:
            if coffee_id not in managed_ids:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé pour ce café")
            query = query.where(DailyTimeRecord.coffee_id == coffee_id)
        else:
            query = query.where(DailyTimeRecord.coffee_id.in_(managed_ids))
    else:
        if coffee_id is not None:
            query = query.where(DailyTimeRecord.coffee_id == coffee_id)

    if start_date is not None:
        query = query.where(DailyTimeRecord.date >= start_date)
    if end_date is not None:
        query = query.where(DailyTimeRecord.date <= end_date)
    query = query.order_by(DailyTimeRecord.date.desc())

    # Fetch ALL matching records (lightweight – no joins) for KPI stats
    all_result = await db.execute(query)
    all_logs = all_result.scalars().all()

    total = len(all_logs)
    pages = math.ceil(total / size) if size > 0 and total > 0 else 0

    # ── Compute KPI stats over all filtered records ────────────────────────
    today = datetime.date.today()
    current_month_start = today.replace(day=1)
    iso_weekday = today.weekday()   # 0 = Monday
    current_week_start = today - datetime.timedelta(days=iso_weekday)

    total_score_sum = 0.0
    month_score_sum = 0.0;  month_count = 0
    week_score_sum  = 0.0;  week_count  = 0
    late_openings   = 0
    early_closures  = 0

    for log in all_logs:
        coffee = coffees.get(log.coffee_id)
        score  = _compute_score(log, coffee)
        total_score_sum += score

        log_date = log.date if isinstance(log.date, datetime.date) else datetime.date.fromisoformat(str(log.date))
        if log_date >= current_month_start:
            month_score_sum += score
            month_count += 1
        if log_date >= current_week_start:
            week_score_sum += score
            week_count += 1

        if coffee:
            if coffee.opening_time and log.opening_time and log.opening_time > coffee.opening_time:
                late_openings += 1
            if coffee.closing_time and log.closing_time and log.closing_time < coffee.closing_time:
                early_closures += 1

    average_score    = round(total_score_sum / total, 2)      if total       > 0 else 0.0
    monthly_average  = round(month_score_sum / month_count, 2) if month_count > 0 else 0.0
    weekly_average   = round(week_score_sum  / week_count,  2) if week_count  > 0 else 0.0

    # ── Slice to current page and enrich ──────────────────────────────────
    page   = max(1, page)
    offset = (page - 1) * size
    page_logs = all_logs[offset: offset + size]

    enriched = []
    for log in page_logs:
        coffee = coffees.get(log.coffee_id)
        score  = _compute_score(log, coffee)
        status_label = _compute_status(score, thr)
        enriched.append({
            "id":            log.id,
            "date":          log.date,
            "opening_time":  log.opening_time,
            "closing_time":  log.closing_time,
            "coffee_id":     log.coffee_id,
            "controller_id": log.controller_id,
            "score":         score,
            "status":        status_label,
        })

    return {
        "items":           enriched,
        "total":           total,
        "page":            page,
        "size":            size,
        "pages":           pages,
        "average_score":   average_score,
        "late_openings":   late_openings,
        "early_closures":  early_closures,
        "monthly_average": monthly_average,
        "weekly_average":  weekly_average,
    }


@router.get("/export-excel")
async def export_daily_logs_excel(
    coffee_id: Optional[int] = None,
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Export daily logs to Excel format."""
    from fastapi.responses import Response
    from sqlalchemy.orm import selectinload
    
    if current_user.role not in [UserRole.ADMIN, UserRole.BOSS, UserRole.MANAGER, UserRole.CONTROLLER]:
        raise HTTPException(status_code=403, detail="Accès refusé")

    # 1. Load thresholds
    thr_result = await db.execute(select(ScheduleThreshold).limit(1))
    thr = thr_result.scalars().first()
    green_min  = thr.green_min  if thr else 100.0
    orange_min = thr.orange_min if thr else 90.0

    # 2. Build query
    query = select(DailyTimeRecord).options(
        selectinload(DailyTimeRecord.coffee),
        selectinload(DailyTimeRecord.controller)
    )
    
    if current_user.role == UserRole.MANAGER:
        managed_ids = [c.id for c in current_user.managed_coffees] if current_user.managed_coffees else []
        if coffee_id is not None:
            if coffee_id not in managed_ids:
                raise HTTPException(status_code=403, detail="Accès non autorisé pour ce café")
            query = query.where(DailyTimeRecord.coffee_id == coffee_id)
        else:
            query = query.where(DailyTimeRecord.coffee_id.in_(managed_ids))
    else:
        if coffee_id is not None:
            query = query.where(DailyTimeRecord.coffee_id == coffee_id)

    if start_date is not None:
        query = query.where(DailyTimeRecord.date >= start_date)
    if end_date is not None:
        query = query.where(DailyTimeRecord.date <= end_date)
        
    query = query.order_by(DailyTimeRecord.date.desc())

    # 3. Execute query
    result = await db.execute(query)
    logs = result.scalars().all()

    def get_log_status(score: float) -> str:
        if score >= green_min:
            return "Conforme"
        if score >= orange_min:
            return "Partiel"
        return "Non Conforme"

    def get_score_style(score: float) -> str:
        if score >= green_min:
            return "GoodStyle"
        if score >= orange_min:
            return "WarningStyle"
        return "BadStyle"

    def escape_xml(val: Any) -> str:
        if val is None:
            return ""
        s = str(val)
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;").replace("'", "&apos;")

    # 4. Generate XML Rows
    rows_xml = []
    for log in logs:
        score = _compute_score(log, log.coffee)
        status_label = get_log_status(score)
        score_style = get_score_style(score)
        coffee_name = log.coffee.name if log.coffee else f"Café #{log.coffee_id}"
        controller_name = log.controller.full_name if log.controller else f"Utilisateur #{log.controller_id}"
        
        date_str = log.date.strftime("%d/%m/%Y") if log.date else ""
        opening = log.opening_time or "--:--"
        closing = log.closing_time or "--:--"

        rows_xml.append(f"""
   <Row ss:Height="20">
    <Cell><Data ss:Type="String">{escape_xml(date_str)}</Data></Cell>
    <Cell><Data ss:Type="String">{escape_xml(coffee_name)}</Data></Cell>
    <Cell><Data ss:Type="String">{escape_xml(opening)}</Data></Cell>
    <Cell><Data ss:Type="String">{escape_xml(closing)}</Data></Cell>
    <Cell ss:StyleID="{score_style}"><Data ss:Type="Number">{round(score)}</Data></Cell>
    <Cell><Data ss:Type="String">{escape_xml(status_label)}</Data></Cell>
    <Cell><Data ss:Type="String">{escape_xml(controller_name)}</Data></Cell>
   </Row>""")

    if start_date and end_date:
        period_text = f"Du {start_date} au {end_date}"
    elif start_date:
        period_text = f"Depuis le {start_date}"
    elif end_date:
        period_text = f"Jusqu'au {end_date}"
    else:
        period_text = "Toutes les dates disponibles"

    export_date_text = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
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
 <Worksheet ss:Name="Registre des Horaires">
  <Table>
   <Row ss:Height="22"><Cell ss:MergeAcross="6" ss:StyleID="SubHeader"><Data ss:Type="String">Registre des Horaires</Data></Cell></Row>
   <Row ss:Height="18">
    <Cell ss:StyleID="BoldText"><Data ss:Type="String">Période :</Data></Cell>
    <Cell ss:MergeAcross="5"><Data ss:Type="String">{escape_xml(period_text)}</Data></Cell>
   </Row>
   <Row ss:Height="18">
    <Cell ss:StyleID="BoldText"><Data ss:Type="String">Date d'export :</Data></Cell>
    <Cell ss:MergeAcross="5"><Data ss:Type="String">{escape_xml(export_date_text)}</Data></Cell>
   </Row>
   <Row ss:Height="18">
    <Cell ss:StyleID="BoldText"><Data ss:Type="String">Généré par :</Data></Cell>
    <Cell ss:MergeAcross="5"><Data ss:Type="String">{escape_xml(generated_by_text)}</Data></Cell>
   </Row>
   <Row ss:Height="15"></Row> <!-- Spacer -->
   <Row ss:Height="20">
    <Cell ss:StyleID="Header"><Data ss:Type="String">Date</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Café</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Ouverture Réelle</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Fermeture Réelle</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Score (%)</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Statut</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Saisi par</Data></Cell>
   </Row>{"".join(rows_xml)}
  </Table>
 </Worksheet>
</Workbook>"""

    date_str = datetime.date.today().strftime("%Y-%m-%d")
    return Response(
        content=workbook_xml,
        media_type="application/vnd.ms-excel",
        headers={
            "Content-Disposition": f"attachment; filename=horaires_export_{date_str}.xls",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )

@router.post("", response_model=schemas.DailyTimeRecordEnriched)
async def create_daily_log(
    *,
    db: AsyncSession = Depends(deps.get_db),
    log_in: schemas.DailyTimeRecordCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Create or update a daily log, returning the record with computed score."""
    if current_user.role not in [UserRole.CONTROLLER, UserRole.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    # Load threshold
    thr_result = await db.execute(select(ScheduleThreshold).limit(1))
    thr = thr_result.scalars().first()

    # Load coffee
    coffee_result = await db.execute(select(Coffee).where(Coffee.id == log_in.coffee_id))
    coffee = coffee_result.scalars().first()

    # Check existing log
    query = select(DailyTimeRecord).where(
        DailyTimeRecord.coffee_id == log_in.coffee_id,
        DailyTimeRecord.date == log_in.date
    )
    result = await db.execute(query)
    existing_log = result.scalars().first()

    if existing_log:
        if log_in.opening_time is not None:
            existing_log.opening_time = log_in.opening_time
        if log_in.closing_time is not None:
            existing_log.closing_time = log_in.closing_time
        existing_log.controller_id = current_user.id
        log = existing_log
    else:
        log = DailyTimeRecord(
            date=log_in.date,
            opening_time=log_in.opening_time,
            closing_time=log_in.closing_time,
            coffee_id=log_in.coffee_id,
            controller_id=current_user.id
        )
        db.add(log)

    await db.commit()
    await db.refresh(log)

    score = _compute_score(log, coffee)
    status_label = _compute_status(score, thr)

    return {
        "id":            log.id,
        "date":          log.date,
        "opening_time":  log.opening_time,
        "closing_time":  log.closing_time,
        "coffee_id":     log.coffee_id,
        "controller_id": log.controller_id,
        "score":         score,
        "status":        status_label,
    }


@router.delete("/{id}")
async def delete_daily_log(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Delete a daily log. Admin only."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators can delete daily logs")

    query = select(DailyTimeRecord).where(DailyTimeRecord.id == id)
    result = await db.execute(query)
    log = result.scalars().first()
    
    if not log:
        raise HTTPException(status_code=404, detail="Daily log not found")

    await db.delete(log)
    await db.commit()
    return {"message": "Daily log deleted successfully", "id": id}
