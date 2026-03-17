from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_token
from app.database import get_db
from app.integrations.google.token_service import GoogleTokenRefreshError, GoogleTokenService
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/role-login")


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

    if token_expiry:
        current_user.google_token_expiry = token_expiry
        await db.commit()

    return access_token
