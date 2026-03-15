from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.rbac import require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.checkin import CheckinComplete, CheckinCreate, CheckinOut
from app.services.checkin_service import CheckinService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/checkins", tags=["Check-ins"])


@router.post("", response_model=CheckinOut)
async def create_checkin(
    payload: CheckinCreate,
    _: User = Depends(require_roles(UserRole.employee, UserRole.manager)),
    db: AsyncSession = Depends(get_db),
) -> CheckinOut:
    checkin = await CheckinService.schedule(payload, db)
    return CheckinOut.model_validate(checkin)


@router.get("", response_model=list[CheckinOut])
async def list_checkins(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CheckinOut]:
    checkins = await CheckinService.list_checkins(current_user, db)
    return [CheckinOut.model_validate(item) for item in checkins]


@router.patch("/{checkin_id}/complete", response_model=CheckinOut)
async def complete_checkin(
    checkin_id: str,
    payload: CheckinComplete,
    _: User = Depends(require_roles(UserRole.manager, UserRole.hr, UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> CheckinOut:
    checkin = await CheckinService.complete(checkin_id, payload, db)
    return CheckinOut.model_validate(checkin)
