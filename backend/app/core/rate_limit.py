from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import get_settings

settings = get_settings()

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_DEFAULT])


def rate_limit_key_func(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if auth_header:
        return f"user:{auth_header[-24:]}"
    return get_remote_address(request)
