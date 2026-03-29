from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
import logging
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler
from app.config import get_settings
from app.core.api_response import error_response, success_response
from app.core.logging_middleware import RequestLoggingMiddleware
from app.core.rate_limit import limiter
from app.core.response_middleware import ResponseEnvelopeMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.routers import auth, users, organizations, goals, checkins, ratings, reviews, ai_router, meetings_router, hr, employees, performance_cycles, dashboard, manager, employee_dashboard, admin

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(title=settings.APP_NAME)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ALLOW_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ResponseEnvelopeMiddleware)

app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(auth.callback_router)
app.include_router(users.router, prefix=settings.API_PREFIX)
app.include_router(organizations.router, prefix=settings.API_PREFIX)
app.include_router(goals.router, prefix=settings.API_PREFIX)
app.include_router(checkins.router, prefix=settings.API_PREFIX)
app.include_router(ratings.router, prefix=settings.API_PREFIX)
app.include_router(reviews.router, prefix=settings.API_PREFIX)
app.include_router(ai_router.router, prefix=settings.API_PREFIX)
app.include_router(meetings_router.router, prefix=settings.API_PREFIX)
app.include_router(hr.router, prefix=settings.API_PREFIX)
app.include_router(employees.router, prefix=settings.API_PREFIX)
app.include_router(performance_cycles.router, prefix=settings.API_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_PREFIX)
app.include_router(manager.router, prefix=settings.API_PREFIX)
app.include_router(employee_dashboard.router, prefix=settings.API_PREFIX)
app.include_router(admin.router, prefix=settings.API_PREFIX)


@app.get("/health")
async def health_check() -> dict:
    return success_response(data={"status": "ok"}, message="Health check passed")


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException):
    return error_response(message="Request failed", error=exc.detail, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError):
    return error_response(message="Validation failed", error=exc.errors(), status_code=422)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_, exc: Exception):
    return error_response(message="Internal server error", error=str(exc), status_code=500)
