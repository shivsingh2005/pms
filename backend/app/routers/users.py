from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.rbac import require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserOut, UserUpdate
from app.services.user_service import UserService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)


@router.get("/team", response_model=list[UserOut])
async def get_team(
    current_user: User = Depends(
        require_roles(UserRole.manager, UserRole.hr, UserRole.leadership, UserRole.admin)
    ),
    db: AsyncSession = Depends(get_db),
) -> list[UserOut]:
    users = await UserService.get_team(current_user, db)
    return [UserOut.model_validate(user) for user in users]


@router.patch("/update", response_model=UserOut)
async def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    if payload.role and current_user.role not in {UserRole.hr, UserRole.admin}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only HR/Admin can change roles")

    updated = await UserService.update_user(current_user, payload, db)
    return UserOut.model_validate(updated)
