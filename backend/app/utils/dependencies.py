from datetime import datetime, timezone
from uuid import UUID
from fastapi import Depends, Header, HTTPException, status
from app.core.role_context import get_default_mode, get_user_roles
from app.models.enums import UserRole
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_token
from app.database import get_db
from app.integrations.google.token_service import GoogleTokenRefreshError, GoogleTokenService
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(token)
    try:
        user_id = UUID(payload["user_id"])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user id in token") from exc

    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_google_access_token(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> str:
    now = datetime.now(timezone.utc)
    persisted_access = (current_user.google_access_token or "").strip()
    if persisted_access and (current_user.google_token_expiry is None or current_user.google_token_expiry > now):
        return persisted_access

    refresh_token = (current_user.google_refresh_token or "").strip()
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Google Calendar is not connected. Complete Google OAuth to store a refresh token.",
        )

    try:
        access_token, token_expiry = await GoogleTokenService.get_google_access_token(refresh_token)
    except GoogleTokenRefreshError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    current_user.google_access_token = access_token
    if token_expiry:
        current_user.google_token_expiry = token_expiry
    await db.commit()

    return access_token


async def get_user_mode(
    current_user: User = Depends(get_current_user),
    x_user_mode: str | None = Header(default=None, convert_underscores=False),
) -> UserRole:
    user_roles = get_user_roles(current_user)
    if not x_user_mode:
        return get_default_mode(current_user)

    if current_user.role != UserRole.manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="x-user-mode is only supported for manager accounts",
        )

    mode = x_user_mode.strip().lower()
    if mode not in {UserRole.employee.value, UserRole.manager.value}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid x-user-mode header")

    requested_mode = UserRole(mode)
    if requested_mode == UserRole.manager and current_user.role != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only managers can use manager mode")

    if requested_mode not in user_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requested mode is not allowed")

    return requested_mode
