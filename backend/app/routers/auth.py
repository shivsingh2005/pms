from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
import json
import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import Request as UrlRequest, urlopen
from urllib.error import HTTPError, URLError
from uuid import UUID
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.api_response import success_response
from app.core.role_context import get_user_roles
from app.core.rate_limit import limiter
from app.core.security import create_access_token, decode_refresh_token
from app.config import get_settings
from app.database import get_db
from app.schemas.auth import (
    AuthUserResponse,
    EmailLoginRequest,
    GoogleConnectionStatusResponse,
    GoogleAuthorizeResponse,
    GoogleTokenExchangeRequest,
    GoogleTokenExchangeResponse,
    RefreshRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService
from app.utils.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])
callback_router = APIRouter(tags=["Auth"])
settings = get_settings()
logger = logging.getLogger(__name__)


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
    access_token = token_payload.get("access_token")
    if isinstance(access_token, str) and access_token.strip():
        current_user.google_access_token = access_token.strip()

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


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    payload: EmailLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    logger.info("Incoming auth login payload", extra={"email": str(payload.email)})
    try:
        token = await AuthService.email_login(payload, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return success_response(data=token.model_dump(), message="Login successful")


@router.get("/me", response_model=AuthUserResponse)
async def auth_me(current_user: User = Depends(get_current_user)) -> AuthUserResponse:
    roles = sorted(get_user_roles(current_user), key=lambda role: role.value)
    return success_response(
        data=AuthUserResponse(
            id=current_user.id,
            email=current_user.email,
            name=current_user.name,
            role=current_user.role,
            roles=roles,
            organization_id=current_user.organization_id,
            manager_id=current_user.manager_id,
            domain=current_user.domain,
            business_unit=current_user.business_unit,
            department=current_user.department,
            title=current_user.title,
            first_login=current_user.first_login,
            onboarding_complete=current_user.onboarding_complete,
            last_active=current_user.last_active.isoformat() if current_user.last_active else None,
        ).model_dump(),
        message="User profile fetched",
    )


@router.post("/onboarding/complete")
async def complete_onboarding(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    current_user.first_login = False
    current_user.onboarding_complete = True
    current_user.last_active = datetime.now(timezone.utc)
    await db.commit()
    return success_response(data={"completed": True}, message="Onboarding marked complete")


@router.post("/refresh")
async def refresh_token(payload: RefreshRequest):
    claims = decode_refresh_token(payload.refresh_token)
    access_token = create_access_token(
        {
            "user_id": claims["user_id"],
            "organization_id": claims["organization_id"],
            "role": claims["role"],
            "roles": claims.get("roles", [claims["role"]]),
        }
    )
    return success_response(data={"access_token": access_token, "token_type": "bearer"}, message="Token refreshed")


@router.get("/google/authorize", response_model=GoogleAuthorizeResponse)
async def google_authorize(
    redirect_to: str = Query(default="/meetings"),
    current_user: User = Depends(get_current_user),
) -> GoogleAuthorizeResponse:
    if not settings.GOOGLE_CLIENT_ID:
        return success_response(data={"authorization_url": ""}, message="GOOGLE_CLIENT_ID is not configured")

    normalized_redirect = redirect_to if redirect_to.startswith("/") and not redirect_to.startswith("//") else "/meetings"

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
        "scope": " ".join(_google_oauth_scopes()),
        "state": f"{current_user.id}|{normalized_redirect}",
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
    now = datetime.now(timezone.utc)
    expiry = current_user.google_token_expiry
    token_is_fresh = bool(current_user.google_access_token and (expiry is None or expiry > now))
    connected = bool((current_user.google_refresh_token or "").strip()) or token_is_fresh

    return success_response(
        data={
            "connected": connected,
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
    redirect_path = "/meetings"

    if error:
        return RedirectResponse(
            _frontend_redirect(redirect_path, {"google_connected": "0", "reason": error}),
            status_code=status.HTTP_302_FOUND,
        )

    if not code or not state:
        return RedirectResponse(
            _frontend_redirect(redirect_path, {"google_connected": "0", "reason": "missing_code_or_state"}),
            status_code=status.HTTP_302_FOUND,
        )

    user_state, parsed_redirect = (state.split("|", 1) + [""])[:2] if "|" in state else (state, "")
    if parsed_redirect.startswith("/") and not parsed_redirect.startswith("//"):
        redirect_path = parsed_redirect

    try:
        user_id = UUID(user_state)
    except ValueError:
        return RedirectResponse(
            _frontend_redirect(redirect_path, {"google_connected": "0", "reason": "invalid_state"}),
            status_code=status.HTTP_302_FOUND,
        )

    user_result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    current_user = user_result.scalar_one_or_none()
    if not current_user:
        return RedirectResponse(
            _frontend_redirect(redirect_path, {"google_connected": "0", "reason": "user_not_found"}),
            status_code=status.HTTP_302_FOUND,
        )

    try:
        token_payload = _exchange_google_code(code, settings.GOOGLE_REDIRECT_URI)
        await _persist_google_tokens(current_user, token_payload, db)
    except HTTPException as exc:
        reason = str(exc.detail).replace(" ", "_")
        return RedirectResponse(
            _frontend_redirect(redirect_path, {"google_connected": "0", "reason": reason}),
            status_code=status.HTTP_302_FOUND,
        )

    return RedirectResponse(
        _frontend_redirect(redirect_path, {"google_connected": "1"}),
        status_code=status.HTTP_302_FOUND,
    )
