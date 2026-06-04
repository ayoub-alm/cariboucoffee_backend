from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime

from app.api import deps
from app.models.models import Audit, Coffee, User, UserRole, AuditAnswer, AuditQuestion, AuditCategory, DailyTimeRecord
from app.schemas import schemas

router = APIRouter()


def _apply_role_filter(query, current_user: User):
    """
    Apply scoped filtering to any query that contains or is joined to the Audit model.
    """
    if current_user.role in (UserRole.ADMIN, UserRole.BOSS):
        return query
    elif current_user.role == UserRole.AUDITOR:
        return query.where(Audit.auditor_id == current_user.id)
    elif current_user.role == UserRole.MANAGER:
        managed_ids = [c.id for c in current_user.managed_coffees] if current_user.managed_coffees else []
        if managed_ids:
            return query.where(Audit.coffee_id.in_(managed_ids))
        return query.where(func.false())
    elif current_user.role == UserRole.VIEWER:
        if current_user.coffee_id:
            return query.where(Audit.coffee_id == current_user.coffee_id)
        return query.where(func.false())
    return query.where(func.false()) # Deny by default


@router.get("", response_model=schemas.KPIData)
async def read_kpi(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    # 1. Total shops - Scoped for Managers/Viewers
    total_coffee_query = select(func.count(Coffee.id))
    if current_user.role == UserRole.MANAGER:
        managed_ids = [c.id for c in current_user.managed_coffees] if current_user.managed_coffees else []
        total_coffee_query = total_coffee_query.where(Coffee.id.in_(managed_ids)) if managed_ids else total_coffee_query.where(func.false())
    elif current_user.role == UserRole.VIEWER:
        if current_user.coffee_id:
            total_coffee_query = total_coffee_query.where(Coffee.id == current_user.coffee_id)
        else:
            total_coffee_query = total_coffee_query.where(func.false())
            
    result = await db.execute(total_coffee_query)
    total_coffee_shops = result.scalar() or 0

    # 2. Total audits
    total_audits_query = _apply_role_filter(select(func.count(Audit.id)), current_user)
    result = await db.execute(total_audits_query)
    total_audits = result.scalar() or 0

    if total_audits == 0:
        return {
            "total_audits": 0,
            "average_score": 0.0,
            "top_performer": None,
            "worst_performer": None,
            "recent_trend": [],
            "scores_per_category": {},
            "compliance_rate": 0.0,
            "total_coffee_shops": total_coffee_shops,
            "audits_this_month": 0,
            "average_score_this_month": 0.0
        }

    # 3. Average score
    avg_score_query = _apply_role_filter(select(func.avg(Audit.score)), current_user)
    result = await db.execute(avg_score_query)
    average_score = result.scalar() or 0.0

    # 4. Compliance rate
    # Fetch thresholds
    from app.models.models import ConformityThreshold
    t_result = await db.execute(select(ConformityThreshold).limit(1))
    thresholds = t_result.scalars().first()
    
    conforme_min = 80.0
    if thresholds and thresholds.conforme_min is not None:
        conforme_min = max(1.0, thresholds.conforme_min)

    compliant_query = _apply_role_filter(
        select(func.count(Audit.id)).where(Audit.score >= conforme_min), current_user
    )
    result = await db.execute(compliant_query)
    compliant_count = result.scalar() or 0
    compliance_rate = (compliant_count / total_audits * 100) if total_audits > 0 else 0.0

    # 5. Trend
    trend_query = _apply_role_filter(
        select(Audit.score).order_by(Audit.created_at.desc()).limit(10), current_user
    )
    result = await db.execute(trend_query)
    recent_trend = result.scalars().all()

    # 6. Top Performer
    top_stmt = _apply_role_filter(
        select(Coffee.name)
        .join(Audit, Coffee.id == Audit.coffee_id), 
        current_user
    )
    top_stmt = top_stmt.group_by(Coffee.id, Coffee.name).order_by(func.avg(Audit.score).desc()).limit(1)
    result = await db.execute(top_stmt)
    top_performer = result.scalar()

    # 7. Worst Performer
    worst_stmt = _apply_role_filter(
        select(Coffee.name)
        .join(Audit, Coffee.id == Audit.coffee_id),
        current_user
    )
    worst_stmt = worst_stmt.group_by(Coffee.id, Coffee.name).order_by(func.avg(Audit.score).asc()).limit(1)
    result = await db.execute(worst_stmt)
    worst_performer = result.scalar()

    first_day_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 8. Monthly stats
    month_query = _apply_role_filter(
        select(func.count(Audit.id)).where(Audit.created_at >= first_day_of_month), current_user
    )
    result = await db.execute(month_query)
    audits_this_month = result.scalar() or 0

    avg_month_query = _apply_role_filter(
        select(func.avg(Audit.score)).where(Audit.created_at >= first_day_of_month), current_user
    )
    result = await db.execute(avg_month_query)
    average_score_this_month = result.scalar() or 0.0

    # 9. Scores per category
    cat_query = _apply_role_filter(
        select(
            AuditCategory.name,
            func.sum(AuditAnswer.value).label("total_val"),
            func.sum(AuditQuestion.weight).label("total_weight"),
        )
        .select_from(AuditAnswer)
        .join(Audit, Audit.id == AuditAnswer.audit_id)
        .join(AuditQuestion, AuditQuestion.id == AuditAnswer.question_id)
        .join(AuditCategory, AuditCategory.id == AuditQuestion.category_id)
        .where(func.lower(AuditAnswer.choice) != 'n/a'),
        current_user
    )
    cat_query = cat_query.group_by(AuditCategory.name)

    
    result = await db.execute(cat_query)
    scores_per_category = {}
    for row in result.all():
        cat_name = row[0]
        total_val = row[1] or 0
        total_weight = row[2] or 1
        scores_per_category[cat_name] = round((total_val / total_weight) * 100, 2) if total_weight > 0 else 0.0


    # 10. Timing scores per coffee for this month
    timing_query = select(DailyTimeRecord, Coffee).join(Coffee, DailyTimeRecord.coffee_id == Coffee.id).where(DailyTimeRecord.date >= first_day_of_month.date())
    timing_result = await db.execute(timing_query)
    
    coffee_timing_stats = {}
    for record, coffee in timing_result.all():
        if coffee.name not in coffee_timing_stats:
            coffee_timing_stats[coffee.name] = {"total_score": 0, "count": 0}
            
        daily_score = 0
        if record.opening_time and coffee.opening_time and record.opening_time <= coffee.opening_time:
            daily_score += 50
        if record.closing_time and coffee.closing_time and record.closing_time >= coffee.closing_time:
            daily_score += 50
            
        coffee_timing_stats[coffee.name]["total_score"] += daily_score
        coffee_timing_stats[coffee.name]["count"] += 1

    timing_scores = {}
    for c_name, stats in coffee_timing_stats.items():
        timing_scores[c_name] = round(stats["total_score"] / stats["count"], 2) if stats["count"] > 0 else 0.0

    return {
        "total_audits": total_audits,
        "average_score": round(average_score, 2),
        "top_performer": top_performer,
        "worst_performer": worst_performer,
        "recent_trend": [round(s, 2) for s in recent_trend],
        "scores_per_category": scores_per_category,
        "compliance_rate": round(compliance_rate, 2),
        "total_coffee_shops": total_coffee_shops,
        "audits_this_month": audits_this_month,
        "average_score_this_month": round(average_score_this_month, 2),
        "timing_scores": timing_scores
    }


@router.get("/export-monthly-excel")
async def export_monthly_excel(
    start_date: str = None,
    end_date: str = None,
    coffee_shop: str = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    from fastapi import HTTPException
    from fastapi.responses import Response
    from sqlalchemy.orm import selectinload
    from app.models.models import ConformityThreshold, ScheduleThreshold

    if current_user.role not in (UserRole.ADMIN, UserRole.BOSS, UserRole.MANAGER):
        raise HTTPException(status_code=403, detail="Accès non autorisé.")

    # 1. Fetch coffees
    coffee_stmt = select(Coffee)
    if current_user.role == UserRole.MANAGER:
        managed_ids = [c.id for c in current_user.managed_coffees] if current_user.managed_coffees else []
        if not managed_ids:
            raise HTTPException(status_code=400, detail="Vous ne gérez aucun café.")
        coffee_stmt = coffee_stmt.where(Coffee.id.in_(managed_ids))
    
    if coffee_shop:
        coffee_stmt = coffee_stmt.where(Coffee.name == coffee_shop)
        
    c_res = await db.execute(coffee_stmt)
    target_coffees = c_res.scalars().all()

    if not target_coffees:
        raise HTTPException(status_code=404, detail="Aucun café trouvé.")

    # 2. Fetch Audits
    audit_stmt = select(Audit).options(
        selectinload(Audit.coffee),
        selectinload(Audit.auditor)
    )
    if current_user.role == UserRole.MANAGER:
        managed_ids = [c.id for c in current_user.managed_coffees] if current_user.managed_coffees else []
        audit_stmt = audit_stmt.where(Audit.coffee_id.in_(managed_ids))
    elif current_user.role == UserRole.AUDITOR:
        audit_stmt = audit_stmt.where(Audit.auditor_id == current_user.id)
    
    if coffee_shop:
        audit_stmt = audit_stmt.where(Audit.coffee_id.in_([c.id for c in target_coffees]))

    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        audit_stmt = audit_stmt.where(Audit.date >= start_dt)
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        audit_stmt = audit_stmt.where(Audit.date <= end_dt)
        
    audit_stmt = audit_stmt.order_by(Audit.date.desc())
    a_res = await db.execute(audit_stmt)
    audits = a_res.scalars().all()

    # 3. Fetch Daily Time Records
    log_stmt = select(DailyTimeRecord).options(
        selectinload(DailyTimeRecord.coffee),
        selectinload(DailyTimeRecord.controller)
    )
    if current_user.role == UserRole.MANAGER:
        managed_ids = [c.id for c in current_user.managed_coffees] if current_user.managed_coffees else []
        log_stmt = log_stmt.where(DailyTimeRecord.coffee_id.in_(managed_ids))
        
    if coffee_shop:
        log_stmt = log_stmt.where(DailyTimeRecord.coffee_id.in_([c.id for c in target_coffees]))

    if start_date:
        start_d = datetime.strptime(start_date, "%Y-%m-%d").date()
        log_stmt = log_stmt.where(DailyTimeRecord.date >= start_d)
    if end_date:
        end_d = datetime.strptime(end_date, "%Y-%m-%d").date()
        log_stmt = log_stmt.where(DailyTimeRecord.date <= end_d)
        
    log_stmt = log_stmt.order_by(DailyTimeRecord.date.desc())
    l_res = await db.execute(log_stmt)
    daily_logs = l_res.scalars().all()

    # 4. Fetch Thresholds
    t_result = await db.execute(select(ConformityThreshold).limit(1))
    thresholds = t_result.scalars().first()
    conforme_min = thresholds.conforme_min if thresholds and thresholds.conforme_min is not None else 80.0

    thr_result = await db.execute(select(ScheduleThreshold).limit(1))
    thr = thr_result.scalars().first()
    green_min = thr.green_min if thr and thr.green_min is not None else 100.0
    orange_min = thr.orange_min if thr and thr.orange_min is not None else 90.0

    # Helper function to compute timing record score
    def _time_to_minutes(t: str) -> int:
        try:
            h, m = map(int, t.split(":"))
            return h * 60 + m
        except:
            return 0

    def _compute_log_score(log, coffee) -> float:
        if not coffee or not coffee.opening_time or not coffee.closing_time:
            return 100.0
        if not log.opening_time or not log.closing_time:
            return 0.0
        config_start = _time_to_minutes(coffee.opening_time)
        config_end   = _time_to_minutes(coffee.closing_time)
        config_range = config_end - config_start
        if config_range <= 0:
            return 100.0
        real_start = _time_to_minutes(log.opening_time)
        real_end   = _time_to_minutes(log.closing_time)
        real_range = real_end - real_start
        percentage = (real_range / config_range) * 100.0
        return min(round(percentage, 2), 100.0)

    # Helper functions for conditional formatting StyleIDs
    def get_audit_score_style(score: float, conforme_min: float) -> str:
        if score is None:
            return "NumberStyle"
        if score >= conforme_min:
            return "GoodStyle"
        return "BadStyle"

    def get_schedule_score_style(score: float, green_min: float, orange_min: float) -> str:
        if score is None:
            return "NumberStyle"
        if score >= green_min:
            return "GoodStyle"
        if score >= orange_min:
            return "WarningStyle"
        return "BadStyle"

    def get_combined_score_style(score: float, conforme_min: float) -> str:
        if score is None:
            return "NumberStyle"
        if score >= conforme_min:
            return "GoodStyle"
        return "BadStyle"

    # Format period text for top metadata
    if start_date and end_date:
        period_text = f"Du {datetime.strptime(start_date, '%Y-%m-%d').strftime('%d/%m/%Y')} au {datetime.strptime(end_date, '%Y-%m-%d').strftime('%d/%m/%Y')}"
    elif start_date:
        period_text = f"Depuis le {datetime.strptime(start_date, '%Y-%m-%d').strftime('%d/%m/%Y')}"
    elif end_date:
        period_text = f"Jusqu'au {datetime.strptime(end_date, '%Y-%m-%d').strftime('%d/%m/%Y')}"
    else:
        period_text = "Toutes les dates disponibles"

    export_date_text = datetime.now().strftime("%d/%m/%Y %H:%M")
    generated_by_text = current_user.full_name if current_user.full_name else current_user.email

    # ── XML Excel Generator ──
    def escape_xml(val: Any) -> str:
        if val is None:
            return ""
        s = str(val)
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;").replace("'", "&apos;")

    global_rows = []
    coffee_sheets = []

    for coffee in target_coffees:
        # Filter audits for this coffee shop
        shop_audits = [a for a in audits if a.coffee_id == coffee.id]
        audit_count = len(shop_audits)
        audit_avg = sum(a.score for a in shop_audits) / audit_count if audit_count > 0 else None

        # Filter daily logs for this coffee shop
        shop_logs = [l for l in daily_logs if l.coffee_id == coffee.id]
        log_count = len(shop_logs)
        log_avg = sum(_compute_log_score(l, coffee) for l in shop_logs) / log_count if log_count > 0 else None

        # Combined score
        combined_score = 0.0
        if audit_avg is not None and log_avg is not None:
            combined_score = 0.5 * audit_avg + 0.5 * log_avg
        elif audit_avg is not None:
            combined_score = audit_avg
        elif log_avg is not None:
            combined_score = log_avg

        # Determine styles based on scores
        audit_style = get_audit_score_style(audit_avg, conforme_min) if audit_avg is not None else "NumberStyle"
        log_style = get_schedule_score_style(log_avg, green_min, orange_min) if log_avg is not None else "NumberStyle"
        combined_style = get_combined_score_style(combined_score, conforme_min)

        # Add to global KPIs Sheet 1 list
        global_rows.append(f"""
   <Row ss:Height="20">
    <Cell><Data ss:Type="String">{escape_xml(coffee.name)}</Data></Cell>
    <Cell ss:StyleID="{audit_style}"><Data ss:Type="Number">{round(audit_avg) if audit_avg is not None else 0}</Data></Cell>
    <Cell ss:StyleID="NumberStyle"><Data ss:Type="Number">{audit_count}</Data></Cell>
    <Cell ss:StyleID="{log_style}"><Data ss:Type="Number">{round(log_avg) if log_avg is not None else 0}</Data></Cell>
    <Cell ss:StyleID="NumberStyle"><Data ss:Type="Number">{log_count}</Data></Cell>
    <Cell ss:StyleID="{combined_style}"><Data ss:Type="Number">{round(combined_score)}</Data></Cell>
    <Cell ss:StyleID="ChartStyle" ss:Formula="=REPT(&quot;█&quot;,ROUND(RC[-1]/5,0))"><Data ss:Type="String"></Data></Cell>
   </Row>""")

        # Generate separate worksheet details
        compliant_audits = sum(1 for a in shop_audits if a.score >= conforme_min)
        compliance_rate = (compliant_audits / audit_count * 100) if audit_count > 0 else 0.0

        # Excel sheet name cannot contain \ / ? * : [ ] and must be <= 31 chars
        sanitized_name = "".join(c for c in coffee.name if c not in r"\/?*[]:")[:30]
        sheet_xml = f"""
 <Worksheet ss:Name="{escape_xml(sanitized_name)}">
  <Table>
   <!-- Section 1: KPI Summary -->
   <Row ss:Height="22"><Cell ss:MergeAcross="4" ss:StyleID="SubHeader"><Data ss:Type="String">Indicateurs Clés - {escape_xml(coffee.name)}</Data></Cell></Row>
   <Row><Cell ss:StyleID="BoldText"><Data ss:Type="String">KPI</Data></Cell><Cell ss:StyleID="BoldText"><Data ss:Type="String">Valeur</Data></Cell></Row>
   <Row><Cell><Data ss:Type="String">Score Moyen Audits (%)</Data></Cell><Cell ss:StyleID="{audit_style}"><Data ss:Type="Number">{round(audit_avg) if audit_avg is not None else 0}</Data></Cell></Row>
   <Row><Cell><Data ss:Type="String">Taux de Conformité Audits (%)</Data></Cell><Cell ss:StyleID="{get_combined_score_style(compliance_rate, conforme_min)}"><Data ss:Type="Number">{round(compliance_rate)}</Data></Cell></Row>
   <Row><Cell><Data ss:Type="String">Nombre d'Audits</Data></Cell><Cell ss:StyleID="NumberStyle"><Data ss:Type="Number">{audit_count}</Data></Cell></Row>
   <Row><Cell><Data ss:Type="String">Score Moyen Horaires (%)</Data></Cell><Cell ss:StyleID="{log_style}"><Data ss:Type="Number">{round(log_avg) if log_avg is not None else 0}</Data></Cell></Row>
   <Row><Cell><Data ss:Type="String">Total Relevés Horaires</Data></Cell><Cell ss:StyleID="NumberStyle"><Data ss:Type="Number">{log_count}</Data></Cell></Row>
   <Row><Cell><Data ss:Type="String">Score de Conformité Globale (%)</Data></Cell><Cell ss:StyleID="{combined_style}"><Data ss:Type="Number">{round(combined_score)}</Data></Cell></Row>
   <Row ss:Height="15"></Row> <!-- Spacer -->

   <!-- Section 2: Audits Register -->
   <Row ss:Height="22"><Cell ss:MergeAcross="4" ss:StyleID="SubHeader"><Data ss:Type="String">Registre des Audits</Data></Cell></Row>
   <Row ss:Height="20">
    <Cell ss:StyleID="Header"><Data ss:Type="String">Date</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Auditeur</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Score (%)</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Statut</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Workflow</Data></Cell>
   </Row>"""

        if not shop_audits:
            sheet_xml += """
   <Row><Cell ss:MergeAcross="4"><Data ss:Type="String">Aucun audit enregistré</Data></Cell></Row>"""
        else:
            for audit in shop_audits:
                status = "Conforme" if audit.score >= conforme_min else "Non Conforme"
                auditor_name = audit.auditor.full_name if audit.auditor else "N/A"
                this_audit_style = get_audit_score_style(audit.score, conforme_min)
                sheet_xml += f"""
   <Row>
    <Cell><Data ss:Type="String">{audit.date.strftime("%d/%m/%Y") if audit.date else ""}</Data></Cell>
    <Cell><Data ss:Type="String">{escape_xml(auditor_name)}</Data></Cell>
    <Cell ss:StyleID="{this_audit_style}"><Data ss:Type="Number">{round(audit.score)}</Data></Cell>
    <Cell><Data ss:Type="String">{status}</Data></Cell>
    <Cell><Data ss:Type="String">{escape_xml(audit.status.value if hasattr(audit.status, "value") else audit.status)}</Data></Cell>
   </Row>"""

        sheet_xml += f"""
   <Row ss:Height="15"></Row> <!-- Spacer -->

   <!-- Section 3: Daily Logs Register -->
   <Row ss:Height="22"><Cell ss:MergeAcross="6" ss:StyleID="SubHeader"><Data ss:Type="String">Registre des Horaires (Horaires Préconfigurés : {escape_xml(coffee.opening_time or '--:--')} - {escape_xml(coffee.closing_time or '--:--')})</Data></Cell></Row>
   <Row ss:Height="20">
    <Cell ss:StyleID="Header"><Data ss:Type="String">Date</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Ouverture Prévue</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Ouverture Réelle</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Fermeture Prévue</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Fermeture Réelle</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Score (%)</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Statut</Data></Cell>
   </Row>"""

        if not shop_logs:
            sheet_xml += """
   <Row><Cell ss:MergeAcross="6"><Data ss:Type="String">Aucun relevé d'horaires enregistré</Data></Cell></Row>"""
        else:
            for log in shop_logs:
                score = _compute_log_score(log, coffee)
                status = 'Conforme' if score >= green_min else ('Partiel' if score >= orange_min else 'Non Conforme')
                this_log_style = get_schedule_score_style(score, green_min, orange_min)
                sheet_xml += f"""
   <Row>
    <Cell><Data ss:Type="String">{log.date.strftime("%d/%m/%Y") if log.date else ""}</Data></Cell>
    <Cell><Data ss:Type="String">{escape_xml(coffee.opening_time or '--:--')}</Data></Cell>
    <Cell><Data ss:Type="String">{escape_xml(log.opening_time or '--:--')}</Data></Cell>
    <Cell><Data ss:Type="String">{escape_xml(coffee.closing_time or '--:--')}</Data></Cell>
    <Cell><Data ss:Type="String">{escape_xml(log.closing_time or '--:--')}</Data></Cell>
    <Cell ss:StyleID="{this_log_style}"><Data ss:Type="Number">{round(score)}</Data></Cell>
    <Cell><Data ss:Type="String">{status}</Data></Cell>
   </Row>"""

        sheet_xml += """
  </Table>
 </Worksheet>"""
        coffee_sheets.append(sheet_xml)

    # Compile the full XML workbook
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
  <Style ss:ID="ChartStyle">
   <Font ss:FontName="Calibri" ss:Size="10" ss:Color="#005B70" ss:Bold="1"/>
   <Alignment ss:Horizontal="Left" ss:Vertical="Center"/>
  </Style>
 </Styles>
 <Worksheet ss:Name="KPIs Globaux">
  <Table>
   <Row ss:Height="22"><Cell ss:MergeAcross="6" ss:StyleID="SubHeader"><Data ss:Type="String">Synthèse Globale des Établissements</Data></Cell></Row>
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
    <Cell ss:StyleID="Header"><Data ss:Type="String">Café</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Score Moyen Audits (%)</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Nombre d'Audits</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Score Moyen Horaires (%)</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Total Relevés</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Conformité Globale (%)</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Performance</Data></Cell>
   </Row>{"".join(global_rows)}
  </Table>
 </Worksheet>{"".join(coffee_sheets)}
</Workbook>"""

    date_str = datetime.now().strftime("%Y-%m-%d")
    return Response(
        content=workbook_xml,
        media_type="application/vnd.ms-excel",
        headers={
            "Content-Disposition": f"attachment; filename=kpi_mensuels_export_{date_str}.xls",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )
