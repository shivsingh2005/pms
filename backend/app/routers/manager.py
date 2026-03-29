from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.rbac import require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.checkin import ManagerPendingCheckinOut
from app.schemas.manager import ManagerEmployeeInspectionResponse, ManagerTeamMember, ManagerTeamPerformanceResponse
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
