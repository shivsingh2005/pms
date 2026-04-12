from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import require_roles
from app.database import get_db
from app.models.checkin import Checkin
from app.models.enums import UserRole
from app.models.goal import Goal
from app.models.rating import Rating
from app.models.user import User

router = APIRouter(prefix="/hr", tags=["HR"])


@router.get("/employees/{employee_id}")
async def get_hr_employee_profile(
    employee_id: str,
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        employee_uuid = UUID(employee_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid employee id") from exc

    employee = await db.get(User, employee_uuid)
    if (
        employee is None
        or employee.organization_id != current_user.organization_id
        or employee.role != UserRole.employee
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    manager_name: str | None = None
    if employee.manager_id:
        manager = await db.get(User, employee.manager_id)
        if manager and manager.organization_id == current_user.organization_id:
            manager_name = manager.name

    goals_result = await db.execute(
        select(Goal)
        .where(Goal.user_id == employee.id)
        .order_by(Goal.created_at.desc())
    )
    goals = list(goals_result.scalars().all())

    checkins_result = await db.execute(
        select(Checkin)
        .where(Checkin.employee_id == employee.id)
        .order_by(Checkin.created_at.desc())
    )
    checkins = list(checkins_result.scalars().all())

    ratings_result = await db.execute(
        select(Rating)
        .where(Rating.employee_id == employee.id)
        .order_by(Rating.created_at.desc())
    )
    ratings = list(ratings_result.scalars().all())

    trend_week_expr = func.date_trunc("week", Checkin.created_at)
    trend_result = await db.execute(
        select(trend_week_expr, func.coalesce(func.avg(Checkin.overall_progress), 0.0))
        .where(Checkin.employee_id == employee.id)
        .group_by(trend_week_expr)
        .order_by(trend_week_expr.asc())
    )

    avg_progress = round(
        (sum(float(goal.progress or 0.0) for goal in goals) / len(goals)) if goals else 0.0,
        1,
    )
    completed_checkins = sum(
        1 for item in checkins if str(item.status.value if hasattr(item.status, "value") else item.status) in {"submitted", "reviewed"}
    )
    consistency = round((completed_checkins / len(checkins) * 100.0) if checkins else 0.0, 1)
    avg_rating = round(
        (sum(float(item.rating or 0.0) for item in ratings) / len(ratings)) if ratings else 0.0,
        2,
    )

    needs_training = bool(avg_progress < 50 or consistency < 60 or (ratings and avg_rating < 3.0))
    if needs_training:
        ai_training_reason = "Training recommended due to progress, consistency, or rating signals."
    else:
        ai_training_reason = "Current performance signals are stable; continue regular coaching cadence."

    return {
        "id": str(employee.id),
        "name": employee.name,
        "role": employee.title or employee.role.value,
        "department": employee.department or "General",
        "manager_name": manager_name,
        "progress": avg_progress,
        "consistency": consistency,
        "avg_rating": avg_rating,
        "needs_training": needs_training,
        "ai_training_reason": ai_training_reason,
        "goals": [
            {
                "id": str(goal.id),
                "title": goal.title,
                "progress": float(goal.progress or 0.0),
                "status": goal.status.value if hasattr(goal.status, "value") else str(goal.status),
            }
            for goal in goals
        ],
        "checkins": [
            {
                "id": str(item.id),
                "progress": int(item.overall_progress or 0),
                "status": item.status.value if hasattr(item.status, "value") else str(item.status),
                "summary": item.summary,
                "manager_feedback": item.manager_feedback,
                "created_at": item.created_at.isoformat(),
            }
            for item in checkins
        ],
        "ratings": [
            {
                "id": str(item.id),
                "rating": int(item.rating),
                "rating_label": item.rating_label.value if hasattr(item.rating_label, "value") else str(item.rating_label),
                "comments": item.comments,
                "created_at": item.created_at.isoformat(),
            }
            for item in ratings
        ],
        "performance_trend": [
            {
                "week": row[0].date().isoformat() if row[0] is not None else "",
                "progress": round(float(row[1] or 0.0), 1),
            }
            for row in trend_result.all()
        ],
    }


@router.get("/health")
async def health_check(
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
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

    return {
        "status": "ok",
        "organization_id": str(current_user.organization_id),
        "active_users": int(users_result.scalar() or 0),
        "tracked_goals": int(goals_result.scalar() or 0),
    }


@router.get("/overview")
async def get_hr_overview(
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    employee_rows_result = await db.execute(
        select(User)
        .where(
            User.organization_id == current_user.organization_id,
            User.is_active.is_(True),
            User.role == UserRole.employee,
        )
        .order_by(User.name.asc())
    )
    employees = list(employee_rows_result.scalars().all())
    employee_ids = [row.id for row in employees]

    manager_count_result = await db.execute(
        select(func.count(User.id)).where(
            User.organization_id == current_user.organization_id,
            User.is_active.is_(True),
            User.role == UserRole.manager,
        )
    )

    if not employee_ids:
        return {
            "total_employees": 0,
            "total_managers": int(manager_count_result.scalar() or 0),
            "at_risk_employees": 0,
            "avg_org_performance": 0.0,
            "training_heatmap": [],
        }

    goal_summary_result = await db.execute(
        select(
            Goal.user_id,
            func.coalesce(func.avg(Goal.progress), 0.0),
        )
        .where(
            Goal.user_id.in_(employee_ids),
            Goal.status != "rejected",
        )
        .group_by(Goal.user_id)
    )
    goal_avg = {row[0]: float(row[1] or 0.0) for row in goal_summary_result.all()}

    checkin_summary_result = await db.execute(
        select(
            Checkin.employee_id,
            func.count(Checkin.id),
            func.count(Checkin.id).filter(Checkin.status.in_(["submitted", "reviewed"])),
        )
        .where(Checkin.employee_id.in_(employee_ids))
        .group_by(Checkin.employee_id)
    )
    consistency_map = {}
    for employee_id, total, done in checkin_summary_result.all():
        total_count = int(total or 0)
        done_count = int(done or 0)
        consistency_map[employee_id] = (float(done_count) / float(total_count) * 100.0) if total_count else 0.0

    rating_summary_result = await db.execute(
        select(
            Rating.employee_id,
            func.coalesce(func.avg(Rating.rating), 0.0),
        )
        .where(Rating.employee_id.in_(employee_ids))
        .group_by(Rating.employee_id)
    )
    rating_map = {row[0]: float(row[1] or 0.0) for row in rating_summary_result.all()}

    heatmap = []
    at_risk_count = 0
    for employee in employees:
        progress = round(goal_avg.get(employee.id, 0.0), 1)
        consistency = round(consistency_map.get(employee.id, 0.0), 1)
        rating = round(rating_map.get(employee.id, 0.0), 2) if employee.id in rating_map else None

        risk_score = 0
        if progress < 40:
            risk_score += 2
        elif progress < 60:
            risk_score += 1
        if consistency < 50:
            risk_score += 2
        elif consistency < 70:
            risk_score += 1
        if rating is not None and rating < 2.5:
            risk_score += 2
        elif rating is not None and rating < 3.0:
            risk_score += 1

        if risk_score >= 5:
            level = "Critical"
        elif risk_score >= 3:
            level = "High"
        elif risk_score >= 2:
            level = "Medium"
        elif risk_score >= 1:
            level = "Low"
        else:
            level = "No Need"

        needs_training = level in {"High", "Critical"}
        if progress < 40 or needs_training:
            at_risk_count += 1

        heatmap.append(
            {
                "employee_id": str(employee.id),
                "employee_name": employee.name,
                "progress": progress,
                "consistency": consistency,
                "rating": rating,
                "intensity": min(risk_score, 5),
                "training_need_level": level,
                "needs_training": needs_training,
            }
        )

    avg_org_performance = round(sum(goal_avg.get(employee_id, 0.0) for employee_id in employee_ids) / len(employee_ids), 1)

    return {
        "total_employees": len(employee_ids),
        "total_managers": int(manager_count_result.scalar() or 0),
        "at_risk_employees": at_risk_count,
        "avg_org_performance": avg_org_performance,
        "training_heatmap": heatmap,
    }


@router.get("/analytics")
async def get_hr_analytics(
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    employee_ids_result = await db.execute(
        select(User.id, User.department)
        .where(
            User.organization_id == current_user.organization_id,
            User.is_active.is_(True),
            User.role == UserRole.employee,
        )
    )
    employee_rows = employee_ids_result.all()
    employee_ids = [row[0] for row in employee_rows]
    department_map = {row[0]: (row[1] or "General") for row in employee_rows}

    if not employee_ids:
        return {
            "performance_trend": [],
            "department_comparison": [],
            "rating_distribution": [
                {"label": "EE", "count": 0},
                {"label": "DE", "count": 0},
                {"label": "ME", "count": 0},
                {"label": "SME", "count": 0},
                {"label": "NI", "count": 0},
            ],
            "checkin_consistency": [],
        }

    trend_week_expr = func.date_trunc("week", Checkin.created_at)
    trend_result = await db.execute(
        select(
            trend_week_expr,
            func.coalesce(func.avg(Checkin.overall_progress), 0.0),
        )
        .where(Checkin.employee_id.in_(employee_ids))
        .group_by(trend_week_expr)
        .order_by(trend_week_expr.asc())
    )
    performance_trend = [
        {"week": row[0].date().isoformat() if row[0] is not None else "", "value": round(float(row[1] or 0.0), 1)}
        for row in trend_result.all()
    ]

    goals_by_employee_result = await db.execute(
        select(Goal.user_id, func.coalesce(func.avg(Goal.progress), 0.0))
        .where(
            Goal.user_id.in_(employee_ids),
            Goal.status != "rejected",
        )
        .group_by(Goal.user_id)
    )
    goals_by_employee = {row[0]: float(row[1] or 0.0) for row in goals_by_employee_result.all()}

    department_rollup: dict[str, list[float]] = {}
    for employee_id in employee_ids:
        department = department_map.get(employee_id, "General")
        department_rollup.setdefault(department, []).append(goals_by_employee.get(employee_id, 0.0))

    department_comparison = [
        {
            "department": department,
            "value": round(sum(values) / len(values), 1) if values else 0.0,
        }
        for department, values in sorted(department_rollup.items(), key=lambda item: item[0])
    ]

    rating_result = await db.execute(
        select(Rating.rating_label, func.count(Rating.id))
        .where(Rating.employee_id.in_(employee_ids))
        .group_by(Rating.rating_label)
    )
    rating_map = {
        (label.value if hasattr(label, "value") else str(label)): int(count or 0)
        for label, count in rating_result.all()
        if label is not None
    }
    rating_distribution = [
        {"label": "EE", "count": rating_map.get("EE", 0)},
        {"label": "DE", "count": rating_map.get("DE", 0)},
        {"label": "ME", "count": rating_map.get("ME", 0)},
        {"label": "SME", "count": rating_map.get("SME", 0)},
        {"label": "NI", "count": rating_map.get("NI", 0)},
    ]

    consistency_week_expr = func.date_trunc("week", Checkin.created_at)
    checkin_consistency_result = await db.execute(
        select(
            consistency_week_expr,
            func.count(Checkin.id).filter(Checkin.status.in_(["submitted", "reviewed"])),
            func.count(Checkin.id),
        )
        .where(Checkin.employee_id.in_(employee_ids))
        .group_by(consistency_week_expr)
        .order_by(consistency_week_expr.asc())
    )
    checkin_consistency = []
    for week, done, total in checkin_consistency_result.all():
        total_count = int(total or 0)
        done_count = int(done or 0)
        value = round((float(done_count) / float(total_count) * 100.0), 1) if total_count else 0.0
        week_label = week.date().isoformat() if week is not None else ""
        checkin_consistency.append({"week": week_label, "value": value})

    return {
        "performance_trend": performance_trend,
        "department_comparison": department_comparison,
        "rating_distribution": rating_distribution,
        "checkin_consistency": checkin_consistency,
    }


@router.get("/dashboard")
async def get_hr_dashboard_alias(
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    overview = await get_hr_overview(current_user=current_user, db=db)
    analytics = await get_hr_analytics(current_user=current_user, db=db)

    return {
        "total_employees": int(overview.get("total_employees", 0)),
        "avg_performance": float(overview.get("avg_org_performance", 0.0)),
        "at_risk": int(overview.get("at_risk_employees", 0)),
        "need_training": int(sum(1 for row in overview.get("training_heatmap", []) if row.get("needs_training"))),
        "alerts": [],
        "training_heatmap": overview.get("training_heatmap", []),
        "quick_stats": {
            "checkin_rate": float(analytics.get("checkin_consistency", [{}])[-1].get("value", 0.0)) if analytics.get("checkin_consistency") else 0.0,
            "approval_rate": 0.0,
            "rating_rate": float(sum(row.get("count", 0) for row in analytics.get("rating_distribution", []))),
            "meeting_count": 0.0,
        },
    }
