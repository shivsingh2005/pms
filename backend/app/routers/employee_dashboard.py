from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.dashboard import EmployeeDashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/employee", tags=["Employee Dashboard"])


@router.get("/dashboard", response_model=EmployeeDashboardResponse)
async def get_employee_dashboard(
    current_user: User = Depends(require_roles(UserRole.employee)),
    db: AsyncSession = Depends(get_db),
) -> EmployeeDashboardResponse:
    payload = await DashboardService.employee_dashboard(current_user, db)
    return EmployeeDashboardResponse(**payload)
