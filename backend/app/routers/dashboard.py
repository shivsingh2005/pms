from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.checkin import Checkin
from app.models.goal import Goal
from app.models.user import User
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    users_result = await db.execute(
        select(func.count(User.id)).where(
            User.organization_id == current_user.organization_id,
            User.is_active.is_(True),
        )
    )
    goals_result = await db.execute(
        select(func.count(Goal.id)).join(User, Goal.user_id == User.id).where(
            User.organization_id == current_user.organization_id,
            User.is_active.is_(True),
        )
    )
    checkins_result = await db.execute(
        select(func.count(Checkin.id)).join(User, Checkin.employee_id == User.id).where(
            User.organization_id == current_user.organization_id,
            User.is_active.is_(True),
        )
    )

    return {
        "users": int(users_result.scalar() or 0),
        "goals": int(goals_result.scalar() or 0),
        "checkins": int(checkins_result.scalar() or 0),
    }


@router.get("/overview")
async def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get dashboard overview for the current user based on their role."""
    if current_user.role == "employee":
        # Fetch employee-specific metrics
        goals_result = await db.execute(
            select(func.count(Goal.id), func.coalesce(func.avg(Goal.progress), 0.0)).where(
                Goal.user_id == current_user.id
            )
        )
        goals_count, avg_progress = goals_result.one()

        checkins_result = await db.execute(
            select(func.count(Checkin.id)).where(Checkin.employee_id == current_user.id)
        )
        checkins_count = int(checkins_result.scalar() or 0)

        return {
            "employee_id": str(current_user.id),
            "goals_count": int(goals_count or 0),
            "avg_goal_progress": round(float(avg_progress or 0.0), 1),
            "checkins_count": checkins_count,
        }

    # For other roles, return org-wide summary
    return await get_dashboard_summary(current_user, db)


@router.get("/next-action")
async def get_dashboard_next_action(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the next action for the current user based on their role and progress."""
    if current_user.role == "employee":
        # Fetch employee metrics to determine next action
        goals_result = await db.execute(
            select(func.count(Goal.id)).where(Goal.user_id == current_user.id)
        )
        goals_count = int(goals_result.scalar() or 0)

        checkins_result = await db.execute(
            select(func.count(Checkin.id)).where(Checkin.employee_id == current_user.id)
        )
        checkins_count = int(checkins_result.scalar() or 0)

        # Determine next action based on employee state
        if goals_count == 0:
            return {
                "title": "Create your first goal",
                "detail": "Define one measurable goal to start this cycle.",
                "action_url": "/goals",
                "action_label": "Create Goal",
                "level": "warning",
            }

        if checkins_count == 0:
            return {
                "title": "Submit your first check-in",
                "detail": "Share progress so your manager can review your momentum.",
                "action_url": "/checkins",
                "action_label": "Open Check-ins",
                "level": "warning",
            }

        return {
            "title": "You are on track",
            "detail": "Keep updating goals and check-ins to maintain momentum.",
            "action_url": "/employee/dashboard",
            "action_label": "View Dashboard",
            "level": "info",
        }

    # For managers, HR, and leadership - return generic message
    return {
        "title": "Stay aligned with your cycle",
        "detail": "Review your dashboard and complete pending actions.",
        "action_url": "/dashboard",
        "action_label": "Open Dashboard",
        "level": "info",
    }
