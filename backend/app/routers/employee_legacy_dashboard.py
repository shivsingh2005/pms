from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routers.employee_dashboard import _build_employee_dashboard_metrics
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/employee", tags=["Employee Dashboard"])


@router.get("/dashboard", include_in_schema=False)
async def get_employee_dashboard_legacy(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    metrics = await _build_employee_dashboard_metrics(db, current_user.id)

    # Legacy endpoint retained for backward compatibility with older frontend clients.
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
