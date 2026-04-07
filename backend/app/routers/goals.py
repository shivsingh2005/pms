from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.rbac import require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.goal import (
    GoalAssignRequest,
    GoalAssignmentCandidateOut,
    GoalAssignmentOneRequest,
    GoalAssignmentOneResponse,
    GoalAssignmentRecommendationRequest,
    GoalAssignmentRecommendationResponse,
    GoalCascadeRequest,
    GoalCascadeResponse,
    GoalChangeLogOut,
    GoalCreate,
    GoalDriftOut,
    GoalLineageResponse,
    GoalOut,
    GoalUpdate,
)
from app.services.goal_service import GoalService
from app.utils.dependencies import get_current_user, get_user_mode

router = APIRouter(prefix="/goals", tags=["Goals"])


@router.post("", response_model=GoalOut)
async def create_goal(
    payload: GoalCreate,
    current_user: User = Depends(require_roles(UserRole.employee, UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    if current_user.role == UserRole.manager and mode != UserRole.manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Switch to manager mode to create goals as a manager",
        )
    goal = await GoalService.create_goal(current_user, payload, db)
    return GoalOut.model_validate(goal)


@router.get("", response_model=list[GoalOut])
async def list_goals(
    current_user: User = Depends(get_current_user),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> list[GoalOut]:
    goals = await GoalService.list_goals(current_user, mode, db)
    return [GoalOut.model_validate(goal) for goal in goals]


@router.patch("/{goal_id}", response_model=GoalOut)
async def update_goal(
    goal_id: str,
    payload: GoalUpdate,
    current_user: User = Depends(require_roles(UserRole.employee, UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    if current_user.role == UserRole.manager and mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to edit goals")
    goal = await GoalService.update_goal(goal_id, current_user, payload, db)
    return GoalOut.model_validate(goal)


@router.post("/{goal_id}/submit", response_model=GoalOut)
async def submit_goal(
    goal_id: str,
    current_user: User = Depends(require_roles(UserRole.employee, UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    if mode == UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to employee mode to submit personal goals")
    goal = await GoalService.submit_goal(goal_id, current_user, db)
    return GoalOut.model_validate(goal)


@router.post("/{goal_id}/approve", response_model=GoalOut)
async def approve_goal(
    goal_id: str,
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    if current_user.role == UserRole.manager and mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to approve goals")
    goal = await GoalService.approve_goal(goal_id, current_user, db)
    return GoalOut.model_validate(goal)


@router.post("/{goal_id}/reject", response_model=GoalOut)
async def reject_goal(
    goal_id: str,
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    if current_user.role == UserRole.manager and mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to reject goals")
    goal = await GoalService.reject_goal(goal_id, current_user, db)
    return GoalOut.model_validate(goal)


@router.post("/assign", response_model=list[GoalOut])
async def assign_goals(
    payload: GoalAssignRequest,
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> list[GoalOut]:
    if current_user.role == UserRole.manager and mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to assign goals")
    goals = await GoalService.assign_goals(current_user, payload, db)
    return [GoalOut.model_validate(goal) for goal in goals]


@router.post("/assignment/recommendations", response_model=GoalAssignmentRecommendationResponse)
async def get_assignment_recommendations(
    payload: GoalAssignmentRecommendationRequest,
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> GoalAssignmentRecommendationResponse:
    if mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to generate role recommendations")

    output = await GoalService.get_role_goal_recommendations(current_user, payload.organization_objectives, db)
    return GoalAssignmentRecommendationResponse(**output)


@router.get("/assignment/candidates/{role_key}", response_model=list[GoalAssignmentCandidateOut])
async def get_assignment_candidates(
    role_key: str,
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> list[GoalAssignmentCandidateOut]:
    if mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to view candidates")

    rows = await GoalService.list_assignment_candidates(current_user, role_key, db)
    return [GoalAssignmentCandidateOut(**row) for row in rows]


@router.post("/assignment/one", response_model=GoalAssignmentOneResponse)
async def assign_single_goal(
    payload: GoalAssignmentOneRequest,
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> GoalAssignmentOneResponse:
    if mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to assign goals")

    goal, workload, workload_status, warning = await GoalService.assign_single_goal(current_user, payload, db)
    return GoalAssignmentOneResponse(
        goal=GoalOut.model_validate(goal),
        employee_workload_percent=workload,
        employee_workload_status=workload_status,
        warning=warning,
    )


@router.post("/cascade", response_model=GoalCascadeResponse)
async def cascade_goal(
    payload: GoalCascadeRequest,
    current_user: User = Depends(require_roles(UserRole.manager, UserRole.hr, UserRole.leadership)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> GoalCascadeResponse:
    if current_user.role == UserRole.manager and mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to cascade goals")

    parent_goal_id, child_ids = await GoalService.cascade_goal(current_user, payload, db)
    return GoalCascadeResponse(parent_goal_id=parent_goal_id, children_created=len(child_ids), child_goal_ids=child_ids)


@router.get("/lineage/{goal_id}", response_model=GoalLineageResponse)
async def get_goal_lineage(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GoalLineageResponse:
    output = await GoalService.get_goal_lineage(goal_id=goal_id, current_user=current_user, db=db)
    return GoalLineageResponse(**output)


@router.get("/changes/{goal_id}", response_model=list[GoalChangeLogOut])
async def get_goal_changes(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[GoalChangeLogOut]:
    rows = await GoalService.get_goal_changes(goal_id=goal_id, current_user=current_user, db=db)
    return [GoalChangeLogOut.model_validate(row) for row in rows]


@router.get("/insights/drift", response_model=list[GoalDriftOut])
async def get_goal_drift(
    current_user: User = Depends(get_current_user),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> list[GoalDriftOut]:
    rows = await GoalService.get_goal_drift(current_user, mode, db)
    return [GoalDriftOut(**row) for row in rows]
