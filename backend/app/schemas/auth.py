from pydantic import BaseModel, EmailStr
from uuid import UUID
from app.models.enums import UserRole


class RoleLoginRequest(BaseModel):
    role: UserRole = UserRole.employee
    email: EmailStr | None = None
    name: str | None = None
    organization_domain: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class GoogleAuthorizeResponse(BaseModel):
    authorization_url: str


class GoogleTokenExchangeRequest(BaseModel):
    code: str
    redirect_uri: str | None = None


class GoogleTokenExchangeResponse(BaseModel):
    connected: bool
    expires_in: int | None = None
    scope: str | None = None


class GoogleConnectionStatusResponse(BaseModel):
    connected: bool
    token_expiry: str | None = None


class AuthUserResponse(BaseModel):
    id: UUID
    email: EmailStr
    name: str
    role: UserRole
    organization_id: UUID

    model_config = {"from_attributes": True}
