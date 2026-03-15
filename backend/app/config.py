from functools import lru_cache
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "AI-Native PMS Backend"
    API_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:shiv@localhost:5432/pms"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    JWT_SECRET_KEY: str = "change-this-in-production"
    JWT_SECRET: str | None = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    GOOGLE_CALENDAR_SCOPES: str = "https://www.googleapis.com/auth/calendar,https://www.googleapis.com/auth/calendar.events"
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/auth/google/callback"
    SESSION_SECRET: str = "change-this-session-secret"
    GOOGLE_ACCESS_TOKEN: str = ""
    GOOGLE_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3-flash-preview"
    GEMINI_REQUEST_TIMEOUT_SECONDS: int = 30
    GEMINI_MAX_RETRIES: int = 3

    RATE_LIMIT_DEFAULT: str = "100/minute"
    AI_RATE_LIMIT_DEFAULT: str = "30/minute"

    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 300

    CORS_ALLOW_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @model_validator(mode="after")
    def apply_compatibility_aliases(self):
        if self.JWT_SECRET and not self.JWT_SECRET_KEY:
            self.JWT_SECRET_KEY = self.JWT_SECRET
        if self.JWT_SECRET:
            self.JWT_SECRET_KEY = self.JWT_SECRET
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
