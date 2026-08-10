from typing import Any, List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import datetime

from app.api import deps
from app.models.models import DailyTimeRecord, ScheduleThreshold, UserRole, User, Coffee, CoffeeSchedule
from app.schemas import schemas
from app.services.schedule_scoring import (
    compute_schedule_score, score_result_to_dict,
    get_schedule_for_day, _date_to_day_of_week
)

router = APIRouter()


def _resolve_expected_times(coffee: Optional[Coffee], log_date) -> Tuple[Optional[str], Optional[str]]:
    """Resolve the expected opening/closing for a specific date from a coffee's schedules.

    Returns a tuple (expected_opening, expected_closing).
    Special value ("Fermé", "Fermé") signals a closed day.
    Returns (None, None) when no schedule configuration is available.
    """
    if not coffee:
        return None, None

    day_schedule = get_schedule_for_day(
        getattr(coffee, "schedules", None), log_date
    )

    if day_schedule:
        if day_schedule.is_closed:
            return "Fermé", "Fermé"
        return day_schedule.opening_time, day_schedule.closing_time

    # Fall back to single opening/closing time on the Coffee record
    return coffee.opening_time, coffee.closing_time


def _enrich_log(log: DailyTimeRecord, coffee: Optional[Coffee], thr: Optional[ScheduleThreshold]) -> dict:
    result = compute_schedule_score(log, coffee, thr)
    return {
        "id":            log.id,
        "date":          log.date,
        "opening_time":  log.opening_time,
        "closing_time":  log.closing_time,
        "coffee_id":     log.coffee_id,
        "controller_id": log.controller_id,
        **score_result_to_dict(result),
    }


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

    # Load all coffees with their per-day schedules into a dict for fast lookup
    coffees_result = await db.execute(select(Coffee).options(selectinload(Coffee.schedules)))
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
    total_lost_sum  = 0.0
    month_lost_sum  = 0.0;  month_count = 0
    week_lost_sum   = 0.0;  week_count  = 0
    late_openings   = 0
    early_closures  = 0

    for log in all_logs:
        coffee = coffees.get(log.coffee_id)
        result = compute_schedule_score(log, coffee, thr)
        total_score_sum += result.score
        worst_violation = max(result.late_minutes, result.early_minutes)
        total_lost_sum  += worst_violation

        log_date = log.date if isinstance(log.date, datetime.date) else datetime.date.fromisoformat(str(log.date))
        if log_date >= current_month_start:
            month_lost_sum += worst_violation
            month_count += 1
        if log_date >= current_week_start:
            week_lost_sum += worst_violation
            week_count += 1

        if result.is_late_opening:
            late_openings += 1
        if result.is_early_closing:
            early_closures += 1

    average_score       = round(total_score_sum / total, 2)       if total       > 0 else 0.0
    average_lost_minutes = round(total_lost_sum  / total, 2)       if total       > 0 else 0.0
    monthly_average     = round(month_lost_sum  / month_count, 2) if month_count > 0 else 0.0
    weekly_average      = round(week_lost_sum   / week_count,  2) if week_count  > 0 else 0.0

    # ── Slice to current page and enrich ──────────────────────────────────
    page   = max(1, page)
    offset = (page - 1) * size
    page_logs = all_logs[offset: offset + size]

    enriched = []
    for log in page_logs:
        coffee = coffees.get(log.coffee_id)
        enriched.append(_enrich_log(log, coffee, thr))

    return {
        "items":              enriched,
        "total":              total,
        "page":               page,
        "size":               size,
        "pages":              pages,
        "average_score":      average_score,
        "average_lost_minutes": average_lost_minutes,
        "late_openings":      late_openings,
        "early_closures":     early_closures,
        "monthly_average":    monthly_average,
        "weekly_average":     weekly_average,
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
    
    if current_user.role not in [UserRole.ADMIN, UserRole.BOSS, UserRole.MANAGER, UserRole.CONTROLLER]:
        raise HTTPException(status_code=403, detail="Accès refusé")

    # 1. Load thresholds
    thr_result = await db.execute(select(ScheduleThreshold).limit(1))
    thr = thr_result.scalars().first()

    # 2. Build query
    query = select(DailyTimeRecord).options(
        selectinload(DailyTimeRecord.coffee).selectinload(Coffee.schedules),
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

    def get_log_status(result) -> str:
        return result.conformity_label

    def get_score_style(result) -> str:
        if result.status == "green":
            return "GoodStyle"
        if result.status == "orange":
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
        result = compute_schedule_score(log, log.coffee, thr)
        status_label = get_log_status(result)
        score_style = get_score_style(result)
        coffee_name = log.coffee.name if log.coffee else f"Café #{log.coffee_id}"
        controller_name = log.controller.full_name if log.controller else f"Utilisateur #{log.controller_id}"
        
        date_str = log.date.strftime("%d/%m/%Y") if log.date else ""
        opening = log.opening_time or "--:--"
        closing = log.closing_time or "--:--"

        expected_opening = result.expected_opening or "--:--"
        expected_closing = result.expected_closing or "--:--"

        rows_xml.append(f"""
   <Row ss:Height="20">
    <Cell><Data ss:Type="String">{escape_xml(date_str)}</Data></Cell>
    <Cell><Data ss:Type="String">{escape_xml(coffee_name)}</Data></Cell>
    <Cell><Data ss:Type="String">{escape_xml(expected_opening)}</Data></Cell>
    <Cell><Data ss:Type="String">{escape_xml(opening)}</Data></Cell>
    <Cell><Data ss:Type="String">{escape_xml(expected_closing)}</Data></Cell>
    <Cell><Data ss:Type="String">{escape_xml(closing)}</Data></Cell>
    <Cell ss:StyleID="{score_style}"><Data ss:Type="String">{escape_xml(status_label)}</Data></Cell>
    <Cell ss:StyleID="NumberStyle"><Data ss:Type="Number">{round(result.late_minutes)}</Data></Cell>
    <Cell ss:StyleID="NumberStyle"><Data ss:Type="Number">{round(result.early_minutes)}</Data></Cell>
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
   <Row ss:Height="22"><Cell ss:MergeAcross="9" ss:StyleID="SubHeader"><Data ss:Type="String">Registre des Horaires</Data></Cell></Row>
   <Row ss:Height="18">
    <Cell ss:StyleID="BoldText"><Data ss:Type="String">Période :</Data></Cell>
    <Cell ss:MergeAcross="7"><Data ss:Type="String">{escape_xml(period_text)}</Data></Cell>
   </Row>
   <Row ss:Height="18">
    <Cell ss:StyleID="BoldText"><Data ss:Type="String">Date d'export :</Data></Cell>
    <Cell ss:MergeAcross="7"><Data ss:Type="String">{escape_xml(export_date_text)}</Data></Cell>
   </Row>
   <Row ss:Height="18">
    <Cell ss:StyleID="BoldText"><Data ss:Type="String">Généré par :</Data></Cell>
    <Cell ss:MergeAcross="7"><Data ss:Type="String">{escape_xml(generated_by_text)}</Data></Cell>
   </Row>
   <Row ss:Height="15"></Row> <!-- Spacer -->
   <Row ss:Height="20">
    <Cell ss:StyleID="Header"><Data ss:Type="String">Date</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Café</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Ouverture Prévue</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Ouverture Réelle</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Fermeture Prévue</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Fermeture Réelle</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Conformité</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Retard ouv. (min)</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Ferm. anticipée (min)</Data></Cell>
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

    # Load coffee with schedules
    coffee_result = await db.execute(
        select(Coffee).options(selectinload(Coffee.schedules)).where(Coffee.id == log_in.coffee_id)
    )
    coffee = coffee_result.scalars().first()

    # Resolve expected times snapshot once (used below for both new and updated records)
    snap_opening, snap_closing = _resolve_expected_times(coffee, log_in.date)

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
        # Preserve the original snapshot — only fill it in if it was never set
        # (e.g. legacy record being updated for the first time after this migration)
        if not existing_log.expected_opening and snap_opening:
            existing_log.expected_opening = snap_opening
        if not existing_log.expected_closing and snap_closing:
            existing_log.expected_closing = snap_closing
        log = existing_log
    else:
        log = DailyTimeRecord(
            date=log_in.date,
            opening_time=log_in.opening_time,
            closing_time=log_in.closing_time,
            coffee_id=log_in.coffee_id,
            controller_id=current_user.id,
            # Freeze the expected times at creation so future schedule changes
            # do not retroactively affect this record's score.
            expected_opening=snap_opening,
            expected_closing=snap_closing,
        )
        db.add(log)

    await db.commit()
    await db.refresh(log)

    return _enrich_log(log, coffee, thr)


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
