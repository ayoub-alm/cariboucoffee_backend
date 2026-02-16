from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_
from datetime import datetime, timedelta

from app.api import deps
from app.models.models import Audit, Coffee
from app.schemas import schemas

router = APIRouter()

@router.get("", response_model=schemas.KPIData)
async def read_kpi(
    db: AsyncSession = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Get comprehensive KPI data for the dashboard.
    """
    # Total audits
    total_audits_query = select(func.count(Audit.id))
    result = await db.execute(total_audits_query)
    total_audits = result.scalar() or 0

    # Total coffee shops
    total_coffee_query = select(func.count(Coffee.id))
    result = await db.execute(total_coffee_query)
    total_coffee_shops = result.scalar() or 0

    if total_audits == 0:
        return {
            "total_audits": 0,
            "average_score": 0.0,
            "top_performer": None,
            "recent_trend": [],
            "compliance_rate": 0.0,
            "total_coffee_shops": total_coffee_shops,
            "audits_this_month": 0,
            "average_score_this_month": 0.0
        }

    # Average score (all time)
    avg_score_query = select(func.avg(Audit.score))
    result = await db.execute(avg_score_query)
    average_score = result.scalar() or 0.0

    # Compliance rate (score >= 80)
    compliant_query = select(func.count(Audit.id)).where(Audit.score >= 80)
    result = await db.execute(compliant_query)
    compliant_count = result.scalar() or 0
    compliance_rate = (compliant_count / total_audits * 100) if total_audits > 0 else 0.0

    # Recent trend: scores of last 10 audits
    trend_query = select(Audit.score).order_by(Audit.created_at.desc()).limit(10)
    result = await db.execute(trend_query)
    recent_trend = result.scalars().all()

    # Top Performer (Coffee with highest average score)
    stmt = (
        select(Coffee.name)
        .join(Audit, Coffee.id == Audit.coffee_id)
        .group_by(Coffee.id, Coffee.name)
        .order_by(func.avg(Audit.score).desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    top_performer = result.scalar()

    # This month's statistics
    first_day_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Audits this month
    audits_this_month_query = select(func.count(Audit.id)).where(
        Audit.created_at >= first_day_of_month
    )
    result = await db.execute(audits_this_month_query)
    audits_this_month = result.scalar() or 0

    # Average score this month
    avg_score_month_query = select(func.avg(Audit.score)).where(
        Audit.created_at >= first_day_of_month
    )
    result = await db.execute(avg_score_month_query)
    average_score_this_month = result.scalar() or 0.0

    return {
        "total_audits": total_audits,
        "average_score": round(average_score, 2),
        "top_performer": top_performer,
        "recent_trend": [round(s, 2) for s in recent_trend],
        "compliance_rate": round(compliance_rate, 2),
        "total_coffee_shops": total_coffee_shops,
        "audits_this_month": audits_this_month,
        "average_score_this_month": round(average_score_this_month, 2)
    }
