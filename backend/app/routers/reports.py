from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.performance_review import PerformanceReview
from app.models.user import User
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("")
async def list_reports(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(
            PerformanceReview.cycle_year,
            PerformanceReview.cycle_quarter,
            func.count(PerformanceReview.id).label("reviews"),
            func.coalesce(func.avg(PerformanceReview.overall_rating), 0.0).label("avg_rating"),
        )
        .join(User, PerformanceReview.employee_id == User.id)
        .where(User.organization_id == current_user.organization_id)
        .group_by(PerformanceReview.cycle_year, PerformanceReview.cycle_quarter)
        .order_by(PerformanceReview.cycle_year.desc(), PerformanceReview.cycle_quarter.desc())
        .limit(limit)
    )
    rows = result.all()

    return {
        "reports": [
            {
                "cycle_year": row.cycle_year,
                "cycle_quarter": row.cycle_quarter,
                "reviews": int(row.reviews or 0),
                "avg_rating": round(float(row.avg_rating or 0.0), 2),
            }
            for row in rows
        ],
        "total": len(rows),
    }
