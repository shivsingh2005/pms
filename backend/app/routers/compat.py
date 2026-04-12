from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import require_roles
from app.database import get_db
from app.models.aop_manager_assignment import AOPManagerAssignment
from app.models.annual_operating_plan import AnnualOperatingPlan
from app.models.checkin import Checkin
from app.models.goal import Goal
from app.models.meeting import Meeting
from app.models.performance_cycle import PerformanceCycle
from app.models.rating import Rating
from app.models.user import User
from app.models.enums import UserRole
from app.services.goal_service import GoalService
from app.utils.dependencies import get_current_user
from sqlalchemy.orm import aliased

router = APIRouter(tags=["Compatibility"])


class AssignmentItem(BaseModel):
    manager_id: str
    target_value: float = 0.0
    target_percentage: float = 0.0


class AssignManagersPayload(BaseModel):
    assignments: list[AssignmentItem]


class AOPCreatePayload(BaseModel):
    title: str
    description: str | None = None
    total_target_value: float = 0.0
    target_unit: str = "units"
    target_metric: str = "Business impact"
    year: int | None = None
    quarter: int | None = None
    department: str | None = None


class AOPUpdatePayload(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None


class ReportGeneratePayload(BaseModel):
    report_type: str
    employee_id: str | None = None
    manager_id: str | None = None


class FrameworkSelectionPayload(BaseModel):
    selected_framework: str
    cycle_type: str = "quarterly"


class FrameworkPolicyPayload(BaseModel):
    department: str
    allowed_frameworks: list[str]
    cycle_type: str = "quarterly"
    is_active: bool = True


class KpiLibraryPayload(BaseModel):
    role: str
    domain: str | None = None
    department: str | None = None
    goal_title: str
    goal_description: str
    suggested_kpi: str
    suggested_weight: float
    framework: str


class AopPolicyPayload(BaseModel):
    year: int
    objective: str
    target_value: str | None = None
    department: str | None = None


def _goal_cascade_payload(goal: Goal) -> dict:
    return {
        "goal_id": str(goal.id),
        "manager_goal_id": None,
        "aop_id": str(goal.aop_id) if goal.aop_id else None,
        "title": goal.title,
        "description": goal.description,
        "target_value": goal.leadership_target_value,
        "target_unit": goal.leadership_target_unit,
        "target_percentage": None,
        "status": goal.status.value if hasattr(goal.status, "value") else str(goal.status),
        "contribution_level": goal.cascade_source,
    }


def _serialize_datetime(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


async def _build_hr_report_rows(current_user: User, db: AsyncSession) -> list[dict]:
    manager_alias = aliased(User)

    goal_summary = (
        select(
            Goal.user_id.label("employee_id"),
            func.count(Goal.id).label("goal_count"),
            func.coalesce(func.avg(Goal.progress), 0.0).label("avg_progress"),
            func.coalesce(func.sum(Goal.weightage), 0.0).label("current_workload"),
        )
        .where(Goal.status != "rejected")
        .group_by(Goal.user_id)
        .subquery()
    )

    checkin_summary = (
        select(
            Checkin.employee_id.label("employee_id"),
            func.count(Checkin.id).label("checkins_total"),
            func.count(Checkin.id).filter(Checkin.status.in_(["submitted", "reviewed"])).label("checkins_used"),
            func.max(Checkin.created_at).label("last_checkin"),
        )
        .group_by(Checkin.employee_id)
        .subquery()
    )

    rating_summary = (
        select(
            Rating.employee_id.label("employee_id"),
            func.coalesce(func.avg(Rating.rating), 0.0).label("avg_rating"),
        )
        .group_by(Rating.employee_id)
        .subquery()
    )

    result = await db.execute(
        select(
            User.id,
            User.name,
            User.email,
            User.title,
            User.department,
            manager_alias.name.label("manager_name"),
            func.coalesce(goal_summary.c.goal_count, 0).label("goal_count"),
            func.coalesce(goal_summary.c.avg_progress, 0.0).label("avg_progress"),
            func.coalesce(goal_summary.c.current_workload, 0.0).label("current_workload"),
            func.coalesce(checkin_summary.c.checkins_total, 0).label("checkins_total"),
            func.coalesce(checkin_summary.c.checkins_used, 0).label("checkins_used"),
            checkin_summary.c.last_checkin,
            func.coalesce(rating_summary.c.avg_rating, 0.0).label("avg_rating"),
        )
        .outerjoin(manager_alias, User.manager_id == manager_alias.id)
        .outerjoin(goal_summary, goal_summary.c.employee_id == User.id)
        .outerjoin(checkin_summary, checkin_summary.c.employee_id == User.id)
        .outerjoin(rating_summary, rating_summary.c.employee_id == User.id)
        .where(
            User.organization_id == current_user.organization_id,
            User.is_active.is_(True),
            User.role == UserRole.employee,
        )
        .order_by(User.name.asc())
    )

    rows: list[dict] = []
    for row in result.all():
        goal_count = int(row.goal_count or 0)
        avg_progress = round(float(row.avg_progress or 0.0), 1)
        current_workload = round(float(row.current_workload or 0.0), 1)
        checkins_total = int(row.checkins_total or 0)
        checkins_used = int(row.checkins_used or 0)
        consistency = round((checkins_used / checkins_total * 100.0) if checkins_total else 0.0, 1)

        rows.append(
            {
                "employee_id": str(row.id),
                "employee_name": row.name,
                "email": row.email,
                "role": row.title or "Employee",
                "department": row.department or "General",
                "manager_name": row.manager_name,
                "goal_count": goal_count,
                "progress": avg_progress,
                "current_workload": current_workload,
                "consistency": consistency,
                "avg_rating": round(float(row.avg_rating or 0.0), 2),
                "checkins_total": checkins_total,
                "checkins_used": checkins_used,
                "last_checkin": _serialize_datetime(row.last_checkin),
            }
        )

    return rows


def _build_hr_team_report_rows(employee_rows: list[dict]) -> list[dict]:
    grouped: dict[str, dict[str, Any]] = {}

    for row in employee_rows:
        manager_name = str(row.get("manager_name") or "Unassigned")
        bucket = grouped.get(manager_name)
        if bucket is None:
            bucket = {
                "manager_name": manager_name,
                "team_size": 0,
                "avg_progress_total": 0.0,
                "avg_rating_total": 0.0,
                "workload_total": 0.0,
                "checkins_total": 0,
                "checkins_used": 0,
                "at_risk_count": 0,
                "departments": set(),
            }
            grouped[manager_name] = bucket

        progress = float(row.get("progress") or 0.0)
        rating = float(row.get("avg_rating") or 0.0)
        workload = float(row.get("current_workload") or 0.0)
        checkins_total = int(row.get("checkins_total") or 0)
        checkins_used = int(row.get("checkins_used") or 0)

        bucket["team_size"] += 1
        bucket["avg_progress_total"] += progress
        bucket["avg_rating_total"] += rating
        bucket["workload_total"] += workload
        bucket["checkins_total"] += checkins_total
        bucket["checkins_used"] += checkins_used
        if progress < 45:
            bucket["at_risk_count"] += 1

        department = row.get("department")
        if department:
            bucket["departments"].add(str(department))

    output: list[dict] = []
    for manager_name, bucket in grouped.items():
        team_size = int(bucket["team_size"] or 0)
        checkins_total = int(bucket["checkins_total"] or 0)
        checkins_used = int(bucket["checkins_used"] or 0)
        output.append(
            {
                "manager_name": manager_name,
                "team_size": team_size,
                "departments": sorted(list(bucket["departments"])),
                "avg_progress": round((bucket["avg_progress_total"] / team_size) if team_size else 0.0, 1),
                "avg_rating": round((bucket["avg_rating_total"] / team_size) if team_size else 0.0, 2),
                "total_workload": round(float(bucket["workload_total"] or 0.0), 1),
                "at_risk_employees": int(bucket["at_risk_count"] or 0),
                "checkin_consistency": round((checkins_used / checkins_total * 100.0) if checkins_total else 0.0, 1),
            }
        )

    return sorted(output, key=lambda item: str(item.get("manager_name") or ""))


def _build_hr_org_report_rows(employee_rows: list[dict]) -> list[dict]:
    total_employees = len(employee_rows)
    total_progress = sum(float(row.get("progress") or 0.0) for row in employee_rows)
    total_rating = sum(float(row.get("avg_rating") or 0.0) for row in employee_rows)
    total_workload = sum(float(row.get("current_workload") or 0.0) for row in employee_rows)
    at_risk_employees = sum(1 for row in employee_rows if float(row.get("progress") or 0.0) < 45)
    total_checkins = sum(int(row.get("checkins_total") or 0) for row in employee_rows)
    used_checkins = sum(int(row.get("checkins_used") or 0) for row in employee_rows)

    by_department: dict[str, int] = {}
    for row in employee_rows:
        department = str(row.get("department") or "General")
        by_department[department] = by_department.get(department, 0) + 1

    return [
        {
            "scope": "organization",
            "total_employees": total_employees,
            "total_departments": len(by_department),
            "avg_progress": round((total_progress / total_employees) if total_employees else 0.0, 1),
            "avg_rating": round((total_rating / total_employees) if total_employees else 0.0, 2),
            "total_workload": round(total_workload, 1),
            "at_risk_employees": at_risk_employees,
            "checkin_consistency": round((used_checkins / total_checkins * 100.0) if total_checkins else 0.0, 1),
            "department_distribution": by_department,
        }
    ]


def _build_hr_report_rows_by_type(report_type: str, employee_rows: list[dict]) -> list[dict]:
    if report_type == "employee":
        return employee_rows
    if report_type == "team":
        return _build_hr_team_report_rows(employee_rows)
    if report_type == "org":
        return _build_hr_org_report_rows(employee_rows)
    return _build_hr_org_report_rows(employee_rows)


@router.get("/manager/checkins")
async def compat_manager_pending_checkins(
    current_user: User = Depends(require_roles(UserRole.manager)),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    result = await db.execute(
        select(Checkin)
        .where(
            Checkin.manager_id == current_user.id,
            Checkin.status == "submitted",
        )
        .order_by(Checkin.created_at.desc())
    )
    rows = list(result.scalars().all())

    employee_ids = [row.employee_id for row in rows if row.employee_id]
    name_map: dict[Any, str] = {}
    if employee_ids:
        user_result = await db.execute(select(User.id, User.name).where(User.id.in_(employee_ids)))
        name_map = {row[0]: row[1] for row in user_result.all()}

    payload = []
    for row in rows:
        payload.append(
            {
                "id": str(row.id),
                "employee_id": str(row.employee_id),
                "employee_name": name_map.get(row.employee_id, "Unknown"),
                "goal_ids": [str(goal_id) for goal_id in (row.goal_ids or [])],
                "goal_titles": [],
                "overall_progress": int(row.overall_progress or 0),
                "summary": row.summary,
                "achievements": row.achievements,
                "blockers": row.blockers,
                "status": "submitted",
                "created_at": row.created_at.isoformat() if row.created_at else datetime.now(timezone.utc).isoformat(),
            }
        )
    return payload


@router.get("/employee/timeline/state")
async def compat_employee_timeline_state(
    employeeId: str | None = Query(default=None),
    cycleId: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
) -> dict:
    return {
        "employee_id": employeeId or str(current_user.id),
        "cycle_id": cycleId,
        "items": [],
    }


@router.get("/employee/goals/cascaded")
async def compat_employee_cascaded_goals(
    current_user: User = Depends(require_roles(UserRole.employee)),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    result = await db.execute(
        select(Goal)
        .where(
            Goal.user_id == current_user.id,
            Goal.source_type != "self_created",
        )
        .order_by(Goal.created_at.desc())
    )
    rows = list(result.scalars().all())
    return [_goal_cascade_payload(row) for row in rows]


@router.post("/employee/goals/{goal_id}/acknowledge")
async def compat_employee_acknowledge_goal(
    goal_id: str,
    current_user: User = Depends(require_roles(UserRole.employee)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        goal_uuid = UUID(goal_id)
    except ValueError:
        return {"acknowledged": False, "goal_id": goal_id}

    goal = await db.get(Goal, goal_uuid)
    if goal is None or goal.user_id != current_user.id:
        return {"acknowledged": False, "goal_id": goal_id}

    return {"acknowledged": True, "goal_id": str(goal.id)}


@router.get("/employee/goals/{goal_id}/lineage")
async def compat_employee_goal_lineage(
    goal_id: str,
    current_user: User = Depends(require_roles(UserRole.employee, UserRole.manager, UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    output = await GoalService.get_goal_lineage(goal_id, current_user, db)
    root_goal_id = output.get("root_goal_id")
    root_goal = await db.get(Goal, root_goal_id) if root_goal_id else None
    if root_goal is None:
        return {
            "employee_goal_id": goal_id,
            "employee_title": "Unknown",
            "employee_progress": 0.0,
            "employee_target_value": None,
            "employee_target_percentage": None,
            "manager_goal_id": None,
            "manager_title": None,
            "manager_target_value": None,
            "manager_progress": None,
            "aop_id": None,
            "aop_title": None,
            "aop_total_value": None,
            "aop_progress": None,
            "contribution_level": None,
            "business_context": None,
        }

    return {
        "employee_goal_id": str(root_goal.id),
        "employee_title": root_goal.title,
        "employee_progress": float(root_goal.progress or 0.0),
        "employee_target_value": root_goal.leadership_target_value,
        "employee_target_percentage": None,
        "manager_goal_id": None,
        "manager_title": None,
        "manager_target_value": None,
        "manager_progress": None,
        "aop_id": str(root_goal.aop_id) if root_goal.aop_id else None,
        "aop_title": None,
        "aop_total_value": None,
        "aop_progress": None,
        "contribution_level": root_goal.cascade_source,
        "business_context": root_goal.description,
    }


@router.get("/hr/managers")
async def compat_hr_managers(
    department: str | None = Query(default=None),
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    stmt = select(User).where(
        User.organization_id == current_user.organization_id,
        User.role == UserRole.manager,
        User.is_active.is_(True),
    )
    if department:
        stmt = stmt.where(User.department == department)
    result = await db.execute(stmt.order_by(User.name.asc()))
    rows = list(result.scalars().all())
    return [
        {
            "id": str(row.id),
            "name": row.name,
            "email": row.email,
            "department": row.department,
            "title": row.title,
        }
        for row in rows
    ]


@router.get("/hr/employees")
async def compat_hr_employees(
    department: str | None = Query(default=None),
    manager_id: str | None = Query(default=None),
    needs_training: bool | None = Query(default=None),
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    stmt = select(User).where(
        User.organization_id == current_user.organization_id,
        User.role == UserRole.employee,
        User.is_active.is_(True),
    )
    if department:
        stmt = stmt.where(User.department == department)
    if manager_id:
        try:
            stmt = stmt.where(User.manager_id == UUID(manager_id))
        except ValueError:
            return []

    employees_result = await db.execute(stmt.order_by(User.name.asc()))
    employees = list(employees_result.scalars().all())
    employee_ids = [row.id for row in employees]

    checkin_result = await db.execute(
        select(
            Checkin.employee_id,
            func.max(Checkin.created_at),
        )
        .where(Checkin.employee_id.in_(employee_ids))
        .group_by(Checkin.employee_id)
    ) if employee_ids else None
    last_checkin_map = {row[0]: row[1].isoformat() if row[1] else None for row in checkin_result.all()} if checkin_result else {}

    goal_result = await db.execute(
        select(Goal.user_id, func.coalesce(func.avg(Goal.progress), 0.0))
        .where(Goal.user_id.in_(employee_ids))
        .group_by(Goal.user_id)
    ) if employee_ids else None
    progress_map = {row[0]: float(row[1] or 0.0) for row in goal_result.all()} if goal_result else {}

    rating_result = await db.execute(
        select(Rating.employee_id, func.coalesce(func.avg(Rating.rating), 0.0))
        .where(Rating.employee_id.in_(employee_ids))
        .group_by(Rating.employee_id)
    ) if employee_ids else None
    rating_map = {row[0]: float(row[1] or 0.0) for row in rating_result.all()} if rating_result else {}

    rows = []
    for employee in employees:
        progress = round(progress_map.get(employee.id, 0.0), 1)
        rating = round(rating_map.get(employee.id, 0.0), 2) if employee.id in rating_map else None
        consistency = progress
        needs_training_flag = progress < 50
        if needs_training is not None and needs_training_flag != needs_training:
            continue

        rows.append(
            {
                "id": str(employee.id),
                "name": employee.name,
                "email": employee.email,
                "role": employee.title or employee.role.value,
                "department": employee.department or "General",
                "manager_name": None,
                "manager_email": None,
                "progress": progress,
                "rating": rating,
                "consistency": consistency,
                "needs_training": needs_training_flag,
                "last_checkin": last_checkin_map.get(employee.id),
            }
        )
    return rows


@router.get("/hr/team/{manager_id}")
async def compat_hr_team(
    manager_id: str,
    department: str | None = Query(default=None),
    role: str | None = Query(default=None),
    performance: str | None = Query(default=None),
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    employees = await compat_hr_employees(
        department=department,
        manager_id=manager_id,
        needs_training=None,
        current_user=current_user,
        db=db,
    )
    rows = []
    for employee in employees:
        status = "On Track" if employee["progress"] >= 70 else "Needs Attention" if employee["progress"] >= 45 else "At Risk"
        if role and employee["role"] != role:
            continue
        if performance and status.lower().replace(" ", "_") != performance.lower():
            continue
        rows.append(
            {
                "id": employee["id"],
                "name": employee["name"],
                "role": employee["role"],
                "department": employee["department"],
                "progress": employee["progress"],
                "consistency": employee["consistency"],
                "last_checkin": employee.get("last_checkin"),
                "last_checkin_status": "reviewed" if employee.get("last_checkin") else "missing",
                "rating": employee["rating"],
                "status": status,
            }
        )
    return rows


@router.get("/hr/team/{manager_id}/insights")
async def compat_hr_team_insights(
    manager_id: str,
    department: str | None = Query(default=None),
    role: str | None = Query(default=None),
    performance: str | None = Query(default=None),
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    team_rows = await compat_hr_team(manager_id, department, role, performance, current_user, db)
    at_risk = sum(1 for row in team_rows if row["status"] == "At Risk")
    return {
        "summary": [
            f"Team members tracked: {len(team_rows)}",
            f"At-risk employees: {at_risk}",
        ]
    }


@router.get("/hr/manager-team/{manager_id}")
async def compat_hr_manager_team(
    manager_id: str,
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    team_rows = await compat_hr_team(manager_id, None, None, None, current_user, db)
    if not team_rows:
        return {
            "manager_id": manager_id,
            "manager_name": "Unknown",
            "team_size": 0,
            "avg_performance": 0.0,
            "consistency": 0.0,
            "at_risk_employees": 0,
            "top_performers": [],
            "low_performers": [],
            "workload_distribution": [],
            "rating_distribution": [],
            "members": [],
        }

    avg_performance = sum(row["progress"] for row in team_rows) / len(team_rows)
    consistency = sum(row["consistency"] for row in team_rows) / len(team_rows)
    top = sorted(team_rows, key=lambda row: row["progress"], reverse=True)[:3]
    low = sorted(team_rows, key=lambda row: row["progress"])[:3]
    return {
        "manager_id": manager_id,
        "manager_name": team_rows[0]["name"],
        "team_size": len(team_rows),
        "avg_performance": round(avg_performance, 1),
        "consistency": round(consistency, 1),
        "at_risk_employees": sum(1 for row in team_rows if row["status"] == "At Risk"),
        "top_performers": [{"employee": row["name"], "score": row["progress"]} for row in top],
        "low_performers": [{"employee": row["name"], "score": row["progress"]} for row in low],
        "workload_distribution": [{"employee": row["name"], "weightage": 0.0} for row in team_rows],
        "rating_distribution": [],
        "members": team_rows,
    }


@router.get("/hr/calibration")
async def compat_hr_calibration(
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    manager_rows = await compat_hr_managers(None, current_user, db)

    org_rating_result = await db.execute(
        select(func.coalesce(func.avg(Rating.rating), 0.0)).join(User, Rating.employee_id == User.id).where(
            User.organization_id == current_user.organization_id,
            User.is_active.is_(True),
        )
    )
    org_avg_rating = round(float(org_rating_result.scalar() or 0.0), 2)

    org_employee_result = await db.execute(
        select(func.count(User.id)).where(
            User.organization_id == current_user.organization_id,
            User.is_active.is_(True),
            User.role == UserRole.employee,
        )
    )
    total_employees = int(org_employee_result.scalar() or 0)

    manager_payloads: list[dict] = []
    total_team_members = 0
    at_risk_employees = 0
    for manager_row in manager_rows:
        team_rows = await compat_hr_team(manager_row["id"], None, None, None, current_user, db)
        ratings = [float(item.get("rating") or 0.0) for item in team_rows if item.get("rating") is not None]
        progress_values = [float(item.get("progress") or 0.0) for item in team_rows]
        consistency_values = [float(item.get("consistency") or 0.0) for item in team_rows]
        last_checkin_values = [str(item.get("last_checkin")) for item in team_rows if item.get("last_checkin")]
        manager_at_risk = sum(1 for item in team_rows if item.get("status") == "At Risk")
        total_team_members += len(team_rows)
        at_risk_employees += manager_at_risk

        avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0.0
        avg_progress = round(sum(progress_values) / len(progress_values), 1) if progress_values else 0.0
        avg_consistency = round(sum(consistency_values) / len(consistency_values), 1) if consistency_values else 0.0
        delta = round(avg_rating - org_avg_rating, 2)
        if delta > 0.25:
            bias_direction = "Higher than org average"
        elif delta < -0.25:
            bias_direction = "Lower than org average"
        else:
            bias_direction = "Aligned with org average"

        manager_payloads.append(
            {
                "manager_id": manager_row["id"],
                "manager_name": manager_row["name"],
                "department": manager_row.get("department"),
                "team_size": len(team_rows),
                "avg_rating": avg_rating,
                "org_avg_rating": org_avg_rating,
                "delta": delta,
                "bias_direction": bias_direction,
                "avg_progress": avg_progress,
                "consistency": avg_consistency,
                "at_risk_employees": manager_at_risk,
                "last_checkin": max(last_checkin_values) if last_checkin_values else None,
                "members": team_rows,
                "top_performers": sorted(team_rows, key=lambda row: float(row.get("progress") or 0.0), reverse=True)[:3],
                "low_performers": sorted(team_rows, key=lambda row: float(row.get("progress") or 0.0))[:3],
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_managers": len(manager_rows),
            "total_employees": total_employees,
            "total_team_members": total_team_members,
            "org_avg_rating": org_avg_rating,
            "at_risk_employees": at_risk_employees,
        },
        "managers": manager_payloads,
    }


@router.get("/hr/reports")
async def compat_hr_reports(
    report_type: str = Query(default="org"),
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    normalized_type = (report_type or "org").strip().lower()
    if normalized_type not in {"employee", "team", "org"}:
        normalized_type = "org"

    employee_rows = await _build_hr_report_rows(current_user, db)
    rows = _build_hr_report_rows_by_type(normalized_type, employee_rows)
    return {
        "report_type": normalized_type,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rows": rows,
    }


@router.get("/hr/meetings")
async def compat_hr_meetings(
    employee_id: str | None = Query(default=None),
    manager_id: str | None = Query(default=None),
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    stmt = (
        select(Meeting)
        .join(User, Meeting.organizer_id == User.id)
        .where(User.organization_id == current_user.organization_id)
        .order_by(Meeting.start_time.desc())
    )
    if employee_id:
        try:
            stmt = stmt.where(Meeting.employee_id == UUID(employee_id))
        except ValueError:
            return []
    if manager_id:
        try:
            stmt = stmt.where(Meeting.manager_id == UUID(manager_id))
        except ValueError:
            return []

    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    return [
        {
            "id": str(row.id),
            "title": row.title,
            "description": row.description,
            "employee_id": str(row.employee_id) if row.employee_id else None,
            "employee_name": None,
            "manager_id": str(row.manager_id) if row.manager_id else None,
            "manager_name": None,
            "start_time": row.start_time.isoformat(),
            "end_time": row.end_time.isoformat(),
            "duration_minutes": max(1, int((row.end_time - row.start_time).total_seconds() // 60)),
            "meeting_type": row.meeting_type.value,
            "mode": "online",
            "notes": row.description,
            "participants": list(row.participants or []),
            "meet_link": row.meet_link or row.google_meet_link,
            "google_event_id": row.google_event_id,
            "summary": row.summary,
            "status": row.status.value,
            "created_by_role": "hr",
            "created_from_checkin": row.checkin_id is not None,
            "rating_given": False,
        }
        for row in rows
    ]


@router.post("/hr/meetings/{meeting_id}/summarize")
async def compat_hr_meeting_summary(
    meeting_id: str,
    payload: dict,
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _ = current_user
    try:
        meeting_uuid = UUID(meeting_id)
    except ValueError:
        return {"meeting_id": meeting_id, "summary": "Invalid meeting id"}

    meeting = await db.get(Meeting, meeting_uuid)
    if meeting is None:
        return {"meeting_id": meeting_id, "summary": "Meeting not found"}

    transcript = str(payload.get("transcript") or "")
    meeting.summary = transcript[:500] if transcript else (meeting.summary or "Summary unavailable")
    await db.commit()
    return {"meeting_id": str(meeting.id), "summary": meeting.summary or "Summary unavailable"}


@router.get("/leadership/aop")
async def compat_leadership_aop_list(
    current_user: User = Depends(require_roles(UserRole.leadership, UserRole.hr)),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    result = await db.execute(
        select(AnnualOperatingPlan)
        .where(AnnualOperatingPlan.organization_id == current_user.organization_id)
        .order_by(AnnualOperatingPlan.created_at.desc())
    )
    rows = list(result.scalars().all())

    output = []
    for row in rows:
        assignment_count_result = await db.execute(
            select(func.count(AOPManagerAssignment.id)).where(AOPManagerAssignment.aop_id == row.id)
        )
        manager_count = int(assignment_count_result.scalar() or 0)
        output.append(
            {
                "id": str(row.id),
                "organization_id": str(row.organization_id),
                "cycle_id": str(row.cycle_id) if row.cycle_id else None,
                "title": row.title,
                "description": row.description,
                "year": row.year,
                "quarter": row.quarter,
                "total_target_value": row.total_target_value or 0.0,
                "target_unit": row.target_unit or "units",
                "target_metric": row.target_metric or "Business impact",
                "department": row.department,
                "status": row.status,
                "created_by": str(row.created_by) if row.created_by else None,
                "created_at": row.created_at.isoformat() if row.created_at else datetime.now(timezone.utc).isoformat(),
                "updated_at": row.updated_at.isoformat() if row.updated_at else datetime.now(timezone.utc).isoformat(),
                "assigned_target_value": row.total_target_value or 0.0,
                "assigned_percentage": 0.0,
                "manager_count": manager_count,
            }
        )
    return output


@router.post("/leadership/aop")
async def compat_leadership_aop_create(
    payload: AOPCreatePayload,
    current_user: User = Depends(require_roles(UserRole.leadership, UserRole.hr)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    cycle_result = await db.execute(
        select(PerformanceCycle)
        .where(PerformanceCycle.organization_id == current_user.organization_id)
        .order_by(PerformanceCycle.created_at.desc())
        .limit(1)
    )
    cycle = cycle_result.scalar_one_or_none()
    if cycle is None:
        raise HTTPException(status_code=400, detail="No performance cycle found to attach AOP")

    row = AnnualOperatingPlan(
        organization_id=current_user.organization_id,
        cycle_id=cycle.id,
        year=payload.year or datetime.now(timezone.utc).year,
        quarter=payload.quarter,
        title=payload.title,
        objective=payload.title,
        description=payload.description,
        total_target_value=payload.total_target_value,
        target_unit=payload.target_unit,
        target_metric=payload.target_metric,
        department=payload.department,
        created_by=current_user.id,
        status="draft",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)

    return {
        "id": str(row.id),
        "organization_id": str(row.organization_id),
        "cycle_id": str(row.cycle_id),
        "title": row.title,
        "description": row.description,
        "year": row.year,
        "quarter": row.quarter,
        "total_target_value": row.total_target_value,
        "target_unit": row.target_unit,
        "target_metric": row.target_metric,
        "department": row.department,
        "status": row.status,
        "created_by": str(row.created_by) if row.created_by else None,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
        "assigned_target_value": row.total_target_value or 0.0,
        "assigned_percentage": 0.0,
        "manager_count": 0,
    }


@router.patch("/leadership/aop/{aop_id}")
async def compat_leadership_aop_update(
    aop_id: str,
    payload: AOPUpdatePayload,
    current_user: User = Depends(require_roles(UserRole.leadership, UserRole.hr)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        aop_uuid = UUID(aop_id)
    except ValueError:
        return {"id": aop_id, "status": "invalid"}

    row = await db.get(AnnualOperatingPlan, aop_uuid)
    if row is None or row.organization_id != current_user.organization_id:
        return {"id": aop_id, "status": "not_found"}

    if payload.title is not None:
        row.title = payload.title
    if payload.description is not None:
        row.description = payload.description
    if payload.status is not None:
        row.status = payload.status

    await db.commit()
    await db.refresh(row)
    return {
        "id": str(row.id),
        "organization_id": str(row.organization_id),
        "cycle_id": str(row.cycle_id),
        "title": row.title,
        "description": row.description,
        "year": row.year,
        "quarter": row.quarter,
        "total_target_value": row.total_target_value or 0.0,
        "target_unit": row.target_unit or "units",
        "target_metric": row.target_metric or "Business impact",
        "department": row.department,
        "status": row.status,
        "created_by": str(row.created_by) if row.created_by else None,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
        "assigned_target_value": row.total_target_value or 0.0,
        "assigned_percentage": 0.0,
        "manager_count": 0,
    }


@router.get("/leadership/aop/{aop_id}/assignments")
async def compat_leadership_aop_assignments(
    aop_id: str,
    current_user: User = Depends(require_roles(UserRole.leadership, UserRole.hr)),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    try:
        aop_uuid = UUID(aop_id)
    except ValueError:
        return []

    aop_row = await db.get(AnnualOperatingPlan, aop_uuid)
    if aop_row is None or aop_row.organization_id != current_user.organization_id:
        return []

    rows_result = await db.execute(
        select(AOPManagerAssignment, User.name, User.department)
        .join(User, AOPManagerAssignment.manager_id == User.id)
        .where(AOPManagerAssignment.aop_id == aop_uuid)
    )
    rows = rows_result.all()

    return [
        {
            "id": str(item.id),
            "aop_id": str(item.aop_id),
            "manager_id": str(item.manager_id),
            "manager_name": manager_name,
            "manager_department": manager_department,
            "assigned_target_value": float(item.assigned_target_value or 0.0),
            "assigned_percentage": float(item.assigned_percentage or 0.0),
            "target_unit": item.target_unit,
            "description": item.description,
            "status": item.status,
            "acknowledged_at": item.acknowledged_at.isoformat() if item.acknowledged_at else None,
        }
        for item, manager_name, manager_department in rows
    ]


@router.post("/leadership/aop/{aop_id}/assign-managers")
async def compat_leadership_aop_assign_managers(
    aop_id: str,
    payload: AssignManagersPayload,
    current_user: User = Depends(require_roles(UserRole.leadership, UserRole.hr)),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    try:
        aop_uuid = UUID(aop_id)
    except ValueError:
        return []

    aop_row = await db.get(AnnualOperatingPlan, aop_uuid)
    if aop_row is None or aop_row.organization_id != current_user.organization_id:
        return []

    for item in payload.assignments:
        try:
            manager_uuid = UUID(item.manager_id)
        except ValueError:
            continue

        existing_result = await db.execute(
            select(AOPManagerAssignment)
            .where(
                AOPManagerAssignment.aop_id == aop_uuid,
                AOPManagerAssignment.manager_id == manager_uuid,
            )
            .limit(1)
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            existing.assigned_target_value = item.target_value
            existing.assigned_percentage = item.target_percentage
            existing.target_unit = aop_row.target_unit
            existing.status = "active"
            continue

        db.add(
            AOPManagerAssignment(
                aop_id=aop_uuid,
                manager_id=manager_uuid,
                assigned_target_value=item.target_value,
                assigned_percentage=item.target_percentage,
                target_unit=aop_row.target_unit,
                status="active",
                created_by=current_user.id,
            )
        )

    await db.commit()
    return await compat_leadership_aop_assignments(aop_id, current_user, db)


@router.get("/leadership/aop/{aop_id}/progress")
async def compat_leadership_aop_progress(
    aop_id: str,
    current_user: User = Depends(require_roles(UserRole.leadership, UserRole.hr)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    assignments = await compat_leadership_aop_assignments(aop_id, current_user, db)
    title = "AOP Target"
    total_target_value = 0.0
    achieved_value = 0.0
    try:
        row = await db.get(AnnualOperatingPlan, UUID(aop_id))
        if row is not None:
            title = row.title
            total_target_value = float(row.total_target_value or 0.0)
    except ValueError:
        pass

    if assignments:
        achieved_value = float(sum(float(item.get("assigned_target_value") or 0.0) for item in assignments))

    achieved_percentage = round((achieved_value / total_target_value * 100.0), 1) if total_target_value > 0 else 0.0

    return {
        "aop_id": aop_id,
        "title": title,
        "total_target_value": total_target_value,
        "achieved_value": achieved_value,
        "achieved_percentage": achieved_percentage,
        "managers": [
            {
                "manager_id": item["manager_id"],
                "manager_name": item["manager_name"],
                "manager_department": item.get("manager_department"),
                "target_value": float(item.get("assigned_target_value", 0.0)),
                "achieved_value": 0.0,
                "achieved_percentage": 0.0,
                "status_label": "On Track",
            }
            for item in assignments
        ],
    }


@router.post("/reports/generate")
async def compat_reports_generate(
    payload: ReportGeneratePayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _ = db
    return {
        "report_type": payload.report_type,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": "Report generated successfully.",
        "sections": [
            {"heading": "Executive Summary", "content": ["No major blockers detected in current data snapshot."]},
        ],
        "metadata": {
            "requested_by": str(current_user.id),
            "employee_id": payload.employee_id,
            "manager_id": payload.manager_id,
        },
    }


@router.get("/performance-cycles/framework/recommend")
async def compat_framework_recommend(
    role: str = Query(...),
    department: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
) -> dict:
    _ = current_user
    framework = "OKR"
    role_key = role.lower()
    dept_key = (department or "").lower()
    if "sales" in role_key or dept_key == "sales":
        framework = "MBO"
    return {
        "recommended_framework": framework,
        "rationale": f"Recommended for role={role} department={department or 'General'}",
    }


@router.get("/performance-cycles/framework/selection")
async def compat_framework_selection_get(
    current_user: User = Depends(get_current_user),
) -> dict:
    return {
        "user_id": str(current_user.id),
        "selected_framework": "OKR",
        "cycle_type": "quarterly",
        "recommendation_reason": None,
    }


@router.post("/performance-cycles/framework/selection")
async def compat_framework_selection_save(
    payload: FrameworkSelectionPayload,
    current_user: User = Depends(get_current_user),
) -> dict:
    return {
        "user_id": str(current_user.id),
        "selected_framework": payload.selected_framework,
        "cycle_type": payload.cycle_type,
        "recommendation_reason": None,
    }


@router.get("/performance-cycles/framework/policies")
async def compat_framework_policies_get(
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    _ = current_user
    return []


@router.post("/performance-cycles/framework/policies")
async def compat_framework_policies_save(
    payload: FrameworkPolicyPayload,
    current_user: User = Depends(get_current_user),
) -> dict:
    _ = current_user
    return {
        "id": "policy",
        "department": payload.department,
        "allowed_frameworks": payload.allowed_frameworks,
        "cycle_type": payload.cycle_type,
        "is_active": payload.is_active,
    }


@router.get("/performance-cycles/kpi-library")
async def compat_kpi_library_get(
    role: str | None = Query(default=None),
    department: str | None = Query(default=None),
    framework: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    _ = current_user
    _ = (role, department, framework)
    return []


@router.post("/performance-cycles/kpi-library")
async def compat_kpi_library_create(
    payload: KpiLibraryPayload,
    current_user: User = Depends(get_current_user),
) -> dict:
    _ = current_user
    return {
        "id": "kpi",
        "role": payload.role,
        "domain": payload.domain,
        "department": payload.department,
        "goal_title": payload.goal_title,
        "goal_description": payload.goal_description,
        "suggested_kpi": payload.suggested_kpi,
        "suggested_weight": payload.suggested_weight,
        "framework": payload.framework,
    }


@router.get("/performance-cycles/aop")
async def compat_cycles_aop_get(
    year: int | None = Query(default=None),
    department: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    result = await db.execute(
        select(AnnualOperatingPlan)
        .where(AnnualOperatingPlan.organization_id == current_user.organization_id)
        .order_by(AnnualOperatingPlan.created_at.desc())
    )
    rows = list(result.scalars().all())
    payload = []
    for row in rows:
        row_year = row.year
        if year is not None and row_year != year:
            continue
        if department:
            row_department = (row.department or "").lower()
            if row_department != department.lower():
                continue
        payload.append(
            {
                "id": str(row.id),
                "organization_id": str(row.organization_id),
                "year": row_year,
                "objective": row.title,
                "target_value": row.target_value,
                "department": row.department,
                "created_by": str(row.created_by) if row.created_by else None,
            }
        )
    return payload


@router.post("/performance-cycles/aop")
async def compat_cycles_aop_create(
    payload: AopPolicyPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    cycle_result = await db.execute(
        select(PerformanceCycle)
        .where(PerformanceCycle.organization_id == current_user.organization_id)
        .order_by(PerformanceCycle.created_at.desc())
        .limit(1)
    )
    cycle = cycle_result.scalar_one_or_none()
    if cycle is None:
        raise HTTPException(status_code=400, detail="No performance cycle found to attach AOP")

    row = AnnualOperatingPlan(
        organization_id=current_user.organization_id,
        cycle_id=cycle.id,
        year=payload.year,
        title=payload.objective,
        objective=payload.objective,
        description=None,
        target_value=payload.target_value,
        department=payload.department,
        created_by=current_user.id,
        status="draft",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {
        "id": str(row.id),
        "organization_id": str(row.organization_id),
        "year": payload.year,
        "objective": payload.objective,
        "target_value": payload.target_value,
        "department": payload.department,
        "created_by": str(current_user.id),
    }
