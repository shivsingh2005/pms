from fastapi import APIRouter, Depends, HTTPException, Request, status
import json
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import Request as UrlRequest, urlopen
from urllib.error import HTTPError, URLError
from uuid import UUID
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.api_response import success_response
from app.core.rate_limit import limiter
from app.core.security import create_access_token, decode_refresh_token
from app.config import get_settings
from app.database import get_db
from app.schemas.auth import (
    AuthUserResponse,
    GoogleConnectionStatusResponse,
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
callback_router = APIRouter(tags=["Auth"])
settings = get_settings()


def _google_oauth_scopes() -> list[str]:
    configured = [
        scope.strip()
        for scope in settings.GOOGLE_CALENDAR_SCOPES.replace(",", " ").split()
        if scope.strip()
    ]
    required = [
        "openid",
        "email",
        "profile",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.events",
    ]
    ordered_unique: list[str] = []
    for scope in [*configured, *required]:
        if scope not in ordered_unique:
            ordered_unique.append(scope)
    return ordered_unique


def _frontend_redirect(path: str, params: dict[str, str] | None = None) -> str:
    base = settings.FRONTEND_BASE_URL.rstrip("/")
    route = path if path.startswith("/") else f"/{path}"
    if not params:
        return f"{base}{route}"
    return f"{base}{route}?{urlencode(params)}"


def _exchange_google_code(code: str, redirect_uri: str) -> dict:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth credentials are not configured",
        )

    body = urlencode(
        {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
    ).encode("utf-8")

    google_request = UrlRequest(
        "https://oauth2.googleapis.com/token",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urlopen(google_request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
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


async def _persist_google_tokens(current_user: User, token_payload: dict, db: AsyncSession) -> None:
    refresh_token = token_payload.get("refresh_token")
    if isinstance(refresh_token, str) and refresh_token.strip():
        current_user.google_refresh_token = refresh_token.strip()

    if not current_user.google_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Google did not return a refresh token. Reconnect with access_type=offline and prompt=consent "
                "to grant calendar offline access."
            ),
        )

    expires_in = token_payload.get("expires_in")
    if isinstance(expires_in, int):
        current_user.google_token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    await db.commit()


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

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
        "scope": " ".join(_google_oauth_scopes()),
        "state": str(current_user.id),
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return success_response(data={"authorization_url": url}, message="Google authorization URL generated")


@router.post("/google/exchange", response_model=GoogleTokenExchangeResponse)
async def google_exchange(
    payload: GoogleTokenExchangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GoogleTokenExchangeResponse:
    token_payload = _exchange_google_code(payload.code, payload.redirect_uri or settings.GOOGLE_REDIRECT_URI)
    await _persist_google_tokens(current_user, token_payload, db)

    return success_response(
        data={
            "connected": True,
            "expires_in": token_payload.get("expires_in"),
            "scope": token_payload.get("scope"),
        },
        message="Google token exchange successful",
    )


@router.get("/google/status", response_model=GoogleConnectionStatusResponse)
async def google_connection_status(current_user: User = Depends(get_current_user)) -> GoogleConnectionStatusResponse:
    return success_response(
        data={
            "connected": bool((current_user.google_refresh_token or "").strip()),
            "token_expiry": current_user.google_token_expiry.isoformat() if current_user.google_token_expiry else None,
        },
        message="Google connection status fetched",
    )


@callback_router.get("/oauth2callback")
async def google_oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    if error:
        return RedirectResponse(
            _frontend_redirect("/meetings", {"google_connected": "0", "reason": error}),
            status_code=status.HTTP_302_FOUND,
        )

    if not code or not state:
        return RedirectResponse(
            _frontend_redirect("/meetings", {"google_connected": "0", "reason": "missing_code_or_state"}),
            status_code=status.HTTP_302_FOUND,
        )

    try:
        user_id = UUID(state)
    except ValueError:
        return RedirectResponse(
            _frontend_redirect("/meetings", {"google_connected": "0", "reason": "invalid_state"}),
            status_code=status.HTTP_302_FOUND,
        )

    user_result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    current_user = user_result.scalar_one_or_none()
    if not current_user:
        return RedirectResponse(
            _frontend_redirect("/meetings", {"google_connected": "0", "reason": "user_not_found"}),
            status_code=status.HTTP_302_FOUND,
        )

    try:
        token_payload = _exchange_google_code(code, settings.GOOGLE_REDIRECT_URI)
        await _persist_google_tokens(current_user, token_payload, db)
    except HTTPException as exc:
        reason = str(exc.detail).replace(" ", "_")
        return RedirectResponse(
            _frontend_redirect("/meetings", {"google_connected": "0", "reason": reason}),
            status_code=status.HTTP_302_FOUND,
        )

    return RedirectResponse(
        _frontend_redirect("/meetings", {"google_connected": "1"}),
        status_code=status.HTTP_302_FOUND,
    )
