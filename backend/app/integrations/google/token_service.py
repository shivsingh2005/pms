import asyncio
import json
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request as UrlRequest, urlopen

from app.config import get_settings

settings = get_settings()


class GoogleTokenRefreshError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


class GoogleTokenService:
    @staticmethod
    def _refresh_token_request(body: bytes) -> dict:
        request = UrlRequest(
            "https://oauth2.googleapis.com/token",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    async def get_google_access_token(refresh_token: str) -> tuple[str, datetime | None]:
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise GoogleTokenRefreshError("Google OAuth credentials are not configured", status_code=500)

        body = urlencode(
            {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            }
        ).encode("utf-8")

        try:
            payload = await asyncio.to_thread(GoogleTokenService._refresh_token_request, body)
        except HTTPError as exc:
            status_code = 403 if exc.code in {400, 401} else 502
            error_payload = exc.read().decode("utf-8") if hasattr(exc, "read") else ""
            raise GoogleTokenRefreshError(
                f"Google access token refresh failed: {error_payload or str(exc)}",
                status_code=status_code,
            ) from exc
        except URLError as exc:
            raise GoogleTokenRefreshError(
                f"Google access token refresh network failure: {exc}",
                status_code=502,
            ) from exc

        access_token = str(payload.get("access_token") or "").strip()
        if not access_token:
            raise GoogleTokenRefreshError("Google token refresh returned an empty access token", status_code=502)

        expiry = None
        expires_in = payload.get("expires_in")
        if isinstance(expires_in, int):
            expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        return access_token, expiry