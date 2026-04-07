from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.dashboard import DashboardNextActionResponse, DashboardOverviewResponse
from app.services.dashboard_service import DashboardService
from app.services.workflow_service import WorkflowService
from app.utils.dependencies import get_current_user, get_user_mode

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> DashboardOverviewResponse:
    overview = await DashboardService.get_overview(current_user, db, mode)
    return DashboardOverviewResponse(**overview)


@router.get("/next-action", response_model=DashboardNextActionResponse)
async def get_next_action(
    current_user: User = Depends(get_current_user),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> DashboardNextActionResponse:
    payload = await WorkflowService.get_next_action(current_user, mode, db)
    return DashboardNextActionResponse(**payload)
