from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.report import ReportGenerateRequest, ReportGenerateResponse
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/generate", response_model=ReportGenerateResponse)
async def generate_report(
    payload: ReportGenerateRequest,
    current_user: User = Depends(require_roles(UserRole.manager, UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> ReportGenerateResponse:
    report = await ReportService.generate(
        current_user=current_user,
        report_type=payload.report_type,
        employee_id=payload.employee_id,
        manager_id=payload.manager_id,
        db=db,
    )
    return ReportGenerateResponse(**report)
