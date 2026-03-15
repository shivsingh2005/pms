from fastapi import APIRouter, Depends, HTTPException, Request, status
import json
from urllib.parse import urlencode
from urllib.request import Request as UrlRequest, urlopen
from urllib.error import HTTPError, URLError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.api_response import success_response
from app.core.rate_limit import limiter
from app.core.security import create_access_token, decode_refresh_token
from app.config import get_settings
from app.database import get_db
from app.schemas.auth import (
    AuthUserResponse,
    GoogleAuthorizeResponse,
    GoogleTokenExchangeRequest,
    GoogleTokenExchangeResponse,
    RoleLoginRequest,
    RefreshRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService
from app.utils.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])
settings = get_settings()


@router.post("/role-login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def role_login(
    request: Request,
    payload: RoleLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    token = await AuthService.role_login(payload, db)
    return success_response(data=token.model_dump(), message="Login successful")


@router.get("/me", response_model=AuthUserResponse)
async def auth_me(current_user: User = Depends(get_current_user)) -> AuthUserResponse:
    return success_response(
        data=AuthUserResponse.model_validate(current_user).model_dump(),
        message="User profile fetched",
    )


@router.post("/refresh")
async def refresh_token(payload: RefreshRequest):
    claims = decode_refresh_token(payload.refresh_token)
    access_token = create_access_token(
        {
            "user_id": claims["user_id"],
            "organization_id": claims["organization_id"],
            "role": claims["role"],
        }
    )
    return success_response(data={"access_token": access_token, "token_type": "bearer"}, message="Token refreshed")


@router.get("/google/authorize", response_model=GoogleAuthorizeResponse)
async def google_authorize(current_user: User = Depends(get_current_user)) -> GoogleAuthorizeResponse:
    if not settings.GOOGLE_CLIENT_ID:
        return success_response(data={"authorization_url": ""}, message="GOOGLE_CLIENT_ID is not configured")

    scopes = [scope.strip() for scope in settings.GOOGLE_CALENDAR_SCOPES.split(",") if scope.strip()]
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
        "scope": " ".join(scopes),
        "state": str(current_user.id),
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return success_response(data={"authorization_url": url}, message="Google authorization URL generated")


@router.post("/google/exchange", response_model=GoogleTokenExchangeResponse)
async def google_exchange(
    payload: GoogleTokenExchangeRequest,
    _: User = Depends(get_current_user),
) -> GoogleTokenExchangeResponse:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth credentials are not configured",
        )

    body = urlencode(
        {
            "code": payload.code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": payload.redirect_uri or settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
    ).encode("utf-8")

    request = UrlRequest(
        "https://oauth2.googleapis.com/token",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=20) as response:
            token_payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        error_payload = exc.read().decode("utf-8") if hasattr(exc, "read") else ""
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google token exchange failed: {error_payload or str(exc)}",
        ) from exc
    except URLError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Google token exchange network failure: {exc}",
        ) from exc

    return success_response(
        data={
            "access_token": token_payload.get("access_token", ""),
            "expires_in": token_payload.get("expires_in"),
            "scope": token_payload.get("scope"),
            "token_type": token_payload.get("token_type", "Bearer"),
            "refresh_token": token_payload.get("refresh_token"),
        },
        message="Google token exchange successful",
    )
