from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.goal_cascade import (
    AOPManagerAssignmentOut,
    AOPProgressOut,
    AssignManagersRequest,
    CascadeToTeamRequest,
    CascadedEmployeeGoalOut,
    CascadedManagerGoalOut,
    GoalLineageImpactOut,
    LeadershipAOPCreateRequest,
    LeadershipAOPOut,
    LeadershipAOPUpdateRequest,
)
from app.services.goal_cascade_service import GoalCascadeService
from app.utils.dependencies import get_current_user, get_user_mode


router = APIRouter(tags=["Goal Cascade"])


@router.get("/leadership/aop", response_model=list[LeadershipAOPOut])
async def list_leadership_aop(
    current_user: User = Depends(require_roles(UserRole.leadership, UserRole.hr)),
    db: AsyncSession = Depends(get_db),
) -> list[LeadershipAOPOut]:
    rows = await GoalCascadeService.list_aop(current_user, db)
    return [LeadershipAOPOut(**row) for row in rows]


@router.post("/leadership/aop", response_model=LeadershipAOPOut)
async def create_leadership_aop(
    payload: LeadershipAOPCreateRequest,
    current_user: User = Depends(require_roles(UserRole.leadership, UserRole.hr)),
    db: AsyncSession = Depends(get_db),
) -> LeadershipAOPOut:
    plan = await GoalCascadeService.create_aop(current_user, payload, db)
    rows = await GoalCascadeService.list_aop(current_user, db)
    matched = next((row for row in rows if row["id"] == str(plan.id)), None)
    return LeadershipAOPOut(**matched) if matched else LeadershipAOPOut(
        id=str(plan.id),
        organization_id=str(plan.organization_id),
        cycle_id=str(plan.cycle_id) if plan.cycle_id else None,
        title=plan.title or plan.objective,
        description=plan.description,
        year=plan.year,
        quarter=plan.quarter,
        total_target_value=float(plan.total_target_value or 0),
        target_unit=plan.target_unit or "units",
        target_metric=plan.target_metric or "business outcome",
        department=plan.department,
        status=plan.status,
        created_by=str(plan.created_by) if plan.created_by else None,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        assigned_target_value=0,
        assigned_percentage=0,
        manager_count=0,
    )


@router.patch("/leadership/aop/{aop_id}", response_model=LeadershipAOPOut)
async def update_leadership_aop(
    aop_id: str,
    payload: LeadershipAOPUpdateRequest,
    current_user: User = Depends(require_roles(UserRole.leadership, UserRole.hr)),
    db: AsyncSession = Depends(get_db),
) -> LeadershipAOPOut:
    plan = await GoalCascadeService.update_aop(aop_id, current_user, payload, db)
    rows = await GoalCascadeService.list_aop(current_user, db)
    matched = next((row for row in rows if row["id"] == str(plan.id)), None)
    return LeadershipAOPOut(**matched)


@router.get("/leadership/aop/{aop_id}/assignments", response_model=list[AOPManagerAssignmentOut])
async def get_aop_assignments(
    aop_id: str,
    current_user: User = Depends(require_roles(UserRole.leadership, UserRole.hr)),
    db: AsyncSession = Depends(get_db),
) -> list[AOPManagerAssignmentOut]:
    rows = await GoalCascadeService.list_aop_assignments(aop_id, current_user, db)
    return [AOPManagerAssignmentOut(**row) for row in rows]


@router.post("/leadership/aop/{aop_id}/assign-managers", response_model=list[AOPManagerAssignmentOut])
async def assign_aop_managers(
    aop_id: str,
    payload: AssignManagersRequest,
    current_user: User = Depends(require_roles(UserRole.leadership, UserRole.hr)),
    db: AsyncSession = Depends(get_db),
) -> list[AOPManagerAssignmentOut]:
    rows = await GoalCascadeService.assign_managers(aop_id, current_user, payload, db)
    return [AOPManagerAssignmentOut(**row) for row in rows]


@router.get("/leadership/aop/{aop_id}/progress", response_model=AOPProgressOut)
async def get_aop_progress(
    aop_id: str,
    current_user: User = Depends(require_roles(UserRole.leadership, UserRole.hr)),
    db: AsyncSession = Depends(get_db),
) -> AOPProgressOut:
    payload = await GoalCascadeService.aop_progress(aop_id, current_user, db)
    return AOPProgressOut(**payload)


@router.get("/manager/cascaded-goals", response_model=list[CascadedManagerGoalOut])
async def get_manager_cascaded_goals(
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> list[CascadedManagerGoalOut]:
    if mode != UserRole.manager:
        return []
    rows = await GoalCascadeService.manager_cascaded_goals(current_user, db)
    return [CascadedManagerGoalOut(**row) for row in rows]


@router.post("/manager/cascaded-goals/{goal_id}/acknowledge")
async def acknowledge_manager_cascaded_goal(
    goal_id: str,
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if mode != UserRole.manager:
        return {"acknowledged": False, "reason": "Switch to manager mode"}
    return await GoalCascadeService.manager_acknowledge(goal_id, current_user, db)


@router.post("/manager/cascaded-goals/{goal_id}/cascade-to-team")
async def cascade_goal_to_team(
    goal_id: str,
    payload: CascadeToTeamRequest,
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if mode != UserRole.manager:
        return {"count": 0, "created_goals": [], "reason": "Switch to manager mode"}
    return await GoalCascadeService.manager_cascade_to_team(goal_id, current_user, payload, db)


@router.get("/employee/goals/cascaded", response_model=list[CascadedEmployeeGoalOut])
async def get_employee_cascaded_goals(
    current_user: User = Depends(require_roles(UserRole.employee, UserRole.manager)),
    db: AsyncSession = Depends(get_db),
) -> list[CascadedEmployeeGoalOut]:
    rows = await GoalCascadeService.employee_cascaded_goals(current_user, db)
    return [CascadedEmployeeGoalOut(**row) for row in rows]


@router.post("/employee/goals/{goal_id}/acknowledge")
async def acknowledge_employee_cascaded_goal(
    goal_id: str,
    current_user: User = Depends(require_roles(UserRole.employee, UserRole.manager)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await GoalCascadeService.employee_acknowledge(goal_id, current_user, db)


@router.get("/employee/goals/{goal_id}/lineage", response_model=GoalLineageImpactOut)
async def get_employee_goal_lineage(
    goal_id: str,
    current_user: User = Depends(require_roles(UserRole.employee, UserRole.manager)),
    db: AsyncSession = Depends(get_db),
) -> GoalLineageImpactOut:
    payload = await GoalCascadeService.employee_goal_lineage(goal_id, current_user, db)
    return GoalLineageImpactOut(**payload)
