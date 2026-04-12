from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.goal import Goal
from app.models.rating import Rating
from app.models.user import User

router = APIRouter(prefix="/leadership", tags=["Leadership"])


@router.get("/dashboard")
async def get_leadership_dashboard(
    current_user: User = Depends(require_roles(UserRole.leadership, UserRole.hr)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    employee_ids_result = await db.execute(
        select(User.id)
        .where(
            User.organization_id == current_user.organization_id,
            User.is_active.is_(True),
            User.role == UserRole.employee,
        )
    )
    employee_ids = list(employee_ids_result.scalars().all())

    if not employee_ids:
        return {
            "org_performance": 0.0,
            "aop_achievement": 0.0,
            "high_performers": 0,
            "at_risk": 0,
            "aop_progress": {"total": 0, "achieved": 0, "by_unit": []},
            "talent_snapshot": {"top_performers": [], "at_risk": []},
        }

    progress_result = await db.execute(
        select(func.coalesce(func.avg(Goal.progress), 0.0))
        .where(
            Goal.user_id.in_(employee_ids),
            Goal.status != "rejected",
        )
    )
    org_performance = round(float(progress_result.scalar() or 0.0), 1)

    user_progress_result = await db.execute(
        select(Goal.user_id, func.coalesce(func.avg(Goal.progress), 0.0))
        .where(
            Goal.user_id.in_(employee_ids),
            Goal.status != "rejected",
        )
        .group_by(Goal.user_id)
    )
    progress_by_user = {row[0]: float(row[1] or 0.0) for row in user_progress_result.all()}

    rating_result = await db.execute(
        select(Rating.employee_id, func.coalesce(func.avg(Rating.rating), 0.0))
        .where(Rating.employee_id.in_(employee_ids))
        .group_by(Rating.employee_id)
    )
    rating_by_user = {row[0]: float(row[1] or 0.0) for row in rating_result.all()}

    users_result = await db.execute(
        select(User.id, User.name, User.department)
        .where(User.id.in_(employee_ids))
    )

    performers = []
    for user_id, name, department in users_result.all():
        performers.append(
            {
                "employee_id": str(user_id),
                "employee_name": name,
                "name": name,
                "department": department or "General",
                "progress": round(progress_by_user.get(user_id, 0.0), 1),
                "rating": round(rating_by_user.get(user_id, 0.0), 2),
                "consistency": round(progress_by_user.get(user_id, 0.0), 1),
            }
        )

    high_performers = sum(1 for row in performers if row["progress"] >= 80 or row["rating"] >= 4.0)
    at_risk = sum(1 for row in performers if row["progress"] < 40 or (row["rating"] > 0 and row["rating"] < 2.5))

    top_performers = sorted(performers, key=lambda row: (row["progress"], row["rating"]), reverse=True)[:5]
    at_risk_talent = sorted(
        [row for row in performers if row["progress"] < 50 or (row["rating"] > 0 and row["rating"] < 3.0)],
        key=lambda row: (row["progress"], row["rating"]),
    )[:5]

    total_targets = len(employee_ids)
    achieved_targets = sum(1 for row in performers if row["progress"] >= 70)

    return {
        "org_performance": org_performance,
        "aop_achievement": org_performance,
        "high_performers": high_performers,
        "at_risk": at_risk,
        "aop_progress": {
            "total": total_targets,
            "achieved": achieved_targets,
            "by_unit": [],
        },
        "talent_snapshot": {
            "top_performers": top_performers,
            "at_risk": at_risk_talent,
        },
    }
