from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime

from app.api import deps
from app.models.models import Audit, Coffee, User, UserRole, AuditAnswer, AuditQuestion, AuditCategory
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
    compliant_query = _apply_role_filter(
        select(func.count(Audit.id)).where(Audit.score >= 80), current_user
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
        "average_score_this_month": round(average_score_this_month, 2)
    }
