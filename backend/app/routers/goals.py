from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.rbac import require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.goal import GoalCreate, GoalOut, GoalUpdate
from app.services.goal_service import GoalService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/goals", tags=["Goals"])


@router.post("", response_model=GoalOut)
async def create_goal(
    payload: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    goal = await GoalService.create_goal(current_user, payload, db)
    return GoalOut.model_validate(goal)


@router.get("", response_model=list[GoalOut])
async def list_goals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[GoalOut]:
    goals = await GoalService.list_goals(current_user, db)
    return [GoalOut.model_validate(goal) for goal in goals]


@router.patch("/{goal_id}", response_model=GoalOut)
async def update_goal(
    goal_id: str,
    payload: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    goal = await GoalService.update_goal(goal_id, current_user, payload, db)
    return GoalOut.model_validate(goal)


@router.post("/{goal_id}/submit", response_model=GoalOut)
async def submit_goal(
    goal_id: str,
    current_user: User = Depends(require_roles(UserRole.employee, UserRole.manager)),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    goal = await GoalService.submit_goal(goal_id, current_user, db)
    return GoalOut.model_validate(goal)


@router.post("/{goal_id}/approve", response_model=GoalOut)
async def approve_goal(
    goal_id: str,
    _: User = Depends(require_roles(UserRole.manager, UserRole.hr, UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    goal = await GoalService.approve_goal(goal_id, db)
    return GoalOut.model_validate(goal)
