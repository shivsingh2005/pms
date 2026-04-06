from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.rbac import require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.schemas.organization import OrganizationAssignUser, OrganizationCreate, OrganizationOut
from app.schemas.user import UserOut
from app.services.organization_service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post("", response_model=OrganizationOut)
async def create_organization(
    payload: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_roles(UserRole.leadership)),
) -> OrganizationOut:
    org = await OrganizationService.create_organization(payload, db)
    return OrganizationOut.model_validate(org)


@router.post("/{org_id}/assign-user", response_model=UserOut)
async def assign_user(
    org_id: str,
    payload: OrganizationAssignUser,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_roles(UserRole.hr, UserRole.leadership)),
) -> UserOut:
    user = await OrganizationService.assign_user(org_id, payload.user_id, db)
    return UserOut.model_validate(user)
