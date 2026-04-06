from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.dashboard import EmployeeDashboardResponse, EmployeeTimelineResponse
from app.schemas.timeline import CycleTimelineResponse
from app.services.dashboard_service import DashboardService
from app.services.timeline_service import TimelineService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/employee", tags=["Employee Dashboard"])


@router.get("/dashboard", response_model=EmployeeDashboardResponse)
async def get_employee_dashboard(
    current_user: User = Depends(require_roles(UserRole.employee)),
    db: AsyncSession = Depends(get_db),
) -> EmployeeDashboardResponse:
    payload = await DashboardService.employee_dashboard(current_user, db)
    return EmployeeDashboardResponse(**payload)


@router.get("/timeline", response_model=EmployeeTimelineResponse)
async def get_employee_timeline(
    current_user: User = Depends(require_roles(UserRole.employee)),
    db: AsyncSession = Depends(get_db),
) -> EmployeeTimelineResponse:
    items = await DashboardService.employee_timeline(current_user, db)
    return EmployeeTimelineResponse(items=items)


@router.get("/timeline/state", response_model=CycleTimelineResponse)
async def get_cycle_timeline(
    employeeId: str | None = None,
    cycleId: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CycleTimelineResponse:
    target_user = current_user

    if employeeId and employeeId != str(current_user.id):
        if current_user.role not in {UserRole.manager, UserRole.hr, UserRole.leadership}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to view another employee timeline")
        row = await db.get(User, employeeId)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        target_user = row

    try:
        payload = await TimelineService.get_or_create_cycle_timeline(target_user, cycleId, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return CycleTimelineResponse(**payload)
