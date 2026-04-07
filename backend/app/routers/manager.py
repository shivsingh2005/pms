from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.rbac import require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.checkin import ManagerPendingCheckinOut
from app.schemas.manager import (
    ManagerEmployeeInspectionResponse,
    ManagerStackRankingResponse,
    ManagerTeamMember,
    ManagerTeamPerformanceResponse,
)
from app.services.checkin_service import CheckinService
from app.services.manager_service import ManagerService
from app.utils.dependencies import get_user_mode

router = APIRouter(prefix="/manager", tags=["Manager"])


@router.get("/team", response_model=list[ManagerTeamMember])
async def get_manager_team(
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> list[ManagerTeamMember]:
    if current_user.role == UserRole.manager and mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to view team")
    team = await ManagerService.list_team(current_user, db)
    return [ManagerTeamMember(**row) for row in team]


@router.get("/employee/{employee_id}", response_model=ManagerEmployeeInspectionResponse)
async def inspect_employee(
    employee_id: str,
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> ManagerEmployeeInspectionResponse:
    if current_user.role == UserRole.manager and mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to inspect employee")

    payload = await ManagerService.inspect_employee(current_user, employee_id, db)
    return ManagerEmployeeInspectionResponse(**payload)


@router.get("/team-performance", response_model=ManagerTeamPerformanceResponse)
async def get_team_performance(
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> ManagerTeamPerformanceResponse:
    if current_user.role == UserRole.manager and mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to view team analytics")

    payload = await ManagerService.get_team_performance(current_user, db)
    return ManagerTeamPerformanceResponse(**payload)


@router.get("/dashboard", response_model=ManagerTeamPerformanceResponse)
async def get_manager_dashboard(
    managerId: UUID | None = Query(default=None),
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> ManagerTeamPerformanceResponse:
    if current_user.role == UserRole.manager and mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to view dashboard")

    resolved_manager_id = managerId or current_user.id

    if current_user.id != resolved_manager_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager ID mismatch")

    payload = await ManagerService.get_team_performance(current_user, db)
    return ManagerTeamPerformanceResponse(**payload)


@router.get("/stack-ranking", response_model=ManagerStackRankingResponse)
async def get_stack_ranking(
    sort_by: str = Query(default="progress", pattern="^(progress|rating|consistency)$"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    at_risk_only: bool = Query(default=False),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> ManagerStackRankingResponse:
    if current_user.role == UserRole.manager and mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to view stack ranking")

    payload = await ManagerService.get_stack_ranking(
        current_user,
        db,
        sort_by=sort_by,
        order=order,
        at_risk_only=at_risk_only,
        limit=limit,
    )
    return ManagerStackRankingResponse(**payload)


@router.get("/checkins", response_model=list[ManagerPendingCheckinOut])
async def get_pending_checkins(
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> list[ManagerPendingCheckinOut]:
    if current_user.role != UserRole.manager or mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to view team check-ins")

    rows = await CheckinService.list_pending_for_manager(current_user, db)
    return [ManagerPendingCheckinOut(**row) for row in rows]
