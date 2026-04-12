from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.checkin import Checkin
from app.models.goal import Goal
from app.models.rating import Rating
from app.models.user import User
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/employee-dashboard", tags=["Employee Dashboard"])


async def _build_employee_dashboard_metrics(db: AsyncSession, user_id) -> dict:
    goals_result = await db.execute(
        select(
            func.count(Goal.id),
            func.coalesce(func.avg(Goal.progress), 0.0),
            func.count(Goal.id).filter(Goal.progress >= 100),
        ).where(Goal.user_id == user_id)
    )
    goals_count, avg_progress, goals_completed = goals_result.one()

    checkins_result = await db.execute(
        select(func.count(Checkin.id)).where(Checkin.employee_id == user_id)
    )
    checkins_count = int(checkins_result.scalar() or 0)

    rating_result = await db.execute(
        select(func.coalesce(func.avg(Rating.rating), 0.0)).where(Rating.employee_id == user_id)
    )
    avg_rating = float(rating_result.scalar() or 0.0)

    avg_progress_value = round(float(avg_progress or 0.0), 1)

    return {
        "goals_count": int(goals_count or 0),
        "goals_completed": int(goals_completed or 0),
        "avg_goal_progress": avg_progress_value,
        "checkins_count": checkins_count,
        "avg_rating": round(avg_rating, 2),
        "consistency": avg_progress_value,
    }


@router.get("/overview")
async def get_employee_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    metrics = await _build_employee_dashboard_metrics(db, current_user.id)
    manager_name = None
    manager_email = None
    manager_title = None

    if current_user.manager_id:
        manager = await db.get(User, current_user.manager_id)
        if manager and manager.organization_id == current_user.organization_id:
            manager_name = manager.name
            manager_email = manager.email
            manager_title = manager.title

    return {
        "employee_id": str(current_user.id),
        "goals_count": metrics["goals_count"],
        "avg_goal_progress": metrics["avg_goal_progress"],
        "checkins_count": metrics["checkins_count"],
        "avg_rating": metrics["avg_rating"],
        "manager_name": manager_name,
        "manager_email": manager_email,
        "manager_title": manager_title,
    }


@router.get("", include_in_schema=False)
async def get_employee_dashboard_legacy_alias(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    metrics = await _build_employee_dashboard_metrics(db, current_user.id)

    # Backward-compatible shape for clients still calling /api/v1/employee-dashboard
    # instead of /api/v1/employee-dashboard/overview.
    return {
        "employee_id": str(current_user.id),
        "overall_progress": metrics["avg_goal_progress"],
        "goals_completed": metrics["goals_completed"],
        "goals_count": metrics["goals_count"],
        "total_checkins": metrics["checkins_count"],
        "checkins_count": metrics["checkins_count"],
        "consistency": metrics["consistency"],
        "avg_rating": metrics["avg_rating"],
    }
