from uuid import UUID
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.core.security import decode_token
from app.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/role-login")
settings = get_settings()


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


def get_google_access_token(
    x_google_access_token: str | None = Header(default=None, alias="X-Google-Access-Token"),
) -> str:
    token = (x_google_access_token or settings.GOOGLE_ACCESS_TOKEN or "").strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Google OAuth access token. Provide X-Google-Access-Token or set GOOGLE_ACCESS_TOKEN in backend .env",
        )

    if token.startswith("AIza"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google API key detected. Meet/Calendar endpoints require a Google OAuth access token (typically starts with ya29.)",
        )

    return token
