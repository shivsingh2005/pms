from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.rbac import require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.goal import GoalAssignRequest, GoalCreate, GoalOut, GoalUpdate
from app.services.goal_service import GoalService
from app.utils.dependencies import get_current_user, get_user_mode

router = APIRouter(prefix="/goals", tags=["Goals"])


@router.post("", response_model=GoalOut)
async def create_goal(
    payload: GoalCreate,
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    if mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only managers can create goals in manager mode")
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
    current_user: User = Depends(require_roles(UserRole.employee, UserRole.manager, UserRole.admin)),
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
    current_user: User = Depends(require_roles(UserRole.manager, UserRole.admin)),
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
    current_user: User = Depends(require_roles(UserRole.manager, UserRole.admin)),
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
    current_user: User = Depends(require_roles(UserRole.manager, UserRole.admin)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> list[GoalOut]:
    if current_user.role == UserRole.manager and mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to assign goals")
    goals = await GoalService.assign_goals(current_user, payload, db)
    return [GoalOut.model_validate(goal) for goal in goals]
